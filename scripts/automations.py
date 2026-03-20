from typing import Optional
import re

import nest_asyncio
from bs4 import BeautifulSoup
from llama_index.core import PromptTemplate
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.workflow import Workflow, Event, step, StartEvent, StopEvent
from llama_index.llms.ollama import Ollama
from pydantic import BaseModel, Field
import asyncio


def run_async(coro):
    nest_asyncio.apply()
    new_loop = asyncio.get_event_loop()
    # new_loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(new_loop)
    try:
        return new_loop.run_until_complete(coro)
    finally:
        pass
        # new_loop.close()


class FacebookPostExtractor:
    """
    Extractor de datos de una publicación de Facebook usando Beautiful Soup.
    Recibe un objeto Tag de BeautifulSoup que representa un post individual.
    NOTA: No puede hacer clic en 'Ver más', por lo que el mensaje puede estar truncado.
    """

    def __init__(self, post_html):
        self.post = BeautifulSoup(post_html, "html.parser")

    def extract_author(self) -> dict:
        """
        Extrae nombre, URL del perfil y URL del avatar del autor.
        """
        author = {"name": None, "profile_url": None, "avatar_url": None}

        # Buscar contenedor del nombre (data-ad-rendering-role="profile_name")
        profile_container = self.post.find('div', attrs={'data-ad-rendering-role': 'profile_name'})
        if profile_container:
            link = profile_container.find('a')
            if link:
                author["name"] = link.get_text(strip=True)
                author["profile_url"] = link.get('href')

        # Avatar: buscar dentro del primer <svg> <image>
        svg_image = self.post.find('svg').find('image') if self.post.find('svg') else None
        if svg_image:
            author["avatar_url"] = svg_image.get('xlink:href')

        return author

    def extract_timestamp(self) -> str:
        """
        Extrae el texto de timestamp relativo buscando spans con patrones de tiempo.
        """
        # Buscar spans que contengan dígitos seguido de espacio y min/h/d/s...
        # Nota: Beautiful Soup no soporta :has-text, así que recorremos todos los spans
        for span in self.post.find_all('span'):
            text = span.get_text(strip=True)
            if re.search(r'\d+\s*(min|h|d|s|min\.|h\.)', text):
                return text

    def extract_message(self) -> str:
        message_div = self.post.find('div', attrs={'data-ad-rendering-role': 'story_message'})
        if not message_div:
            return ""
        return message_div.get_text(separator='\n', strip=True)

        # message_container = self.post.find('div', attrs={'data-ad-rendering-role': 'story_message'})
        # if message_container:
        #     # Extraer todas las líneas con dir="auto"
        #     lines = message_container.find_all('div', attrs={'dir': 'auto'})
        #     full_text = "\n".join([line.get_text(strip=True) for line in lines])
        #     return full_text

    def extract_images(self) -> list:
        """
        Devuelve lista de URLs de imágenes de la publicación (excluye avatar).
        """
        image_urls = []
        # Buscar imágenes cuyo src contenga "scontent" (dominio de CDN de FB)
        images = self.post.find_all('img', src=re.compile(r'scontent'))
        for img in images:
            src = img.get('src')
            # Excluir avatares (por tamaño pequeño) y duplicados
            if src and 's40x40' not in src and src not in image_urls:
                image_urls.append(src)
        return image_urls

    def extract_reactions(self) -> int:
        """
        Intenta obtener el número de reacciones buscando en aria-label o texto cercano.
        """
        # Buscar elemento con aria-label que contenga "Me gusta" y extraer números
        reaction_elem = self.post.find(attrs={'aria-label': re.compile(r'Me gusta')})
        if reaction_elem:
            label = reaction_elem.get('aria-label', '')
            numbers = re.findall(r'\d+', label)
            if numbers:
                return int(numbers[0])

        # Alternativa: buscar botón de like y luego en el padre
        like_button = self.post.find('div', attrs={'aria-label': 'Me gusta'})
        if like_button and like_button.parent:
            text = like_button.parent.get_text(strip=True)
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])

    def extract_comments_count(self) -> int:
        """
        Intenta obtener el número de comentarios.
        """
        comment_button = self.post.find('div', attrs={'aria-label': 'Dejar un comentario'})
        if comment_button and comment_button.parent:
            text = comment_button.parent.get_text(strip=True)
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])

    def extract_shares_count(self) -> int:
        """
        Intenta obtener el número de veces compartido.
        """
        share_button = self.post.find('div', attrs={'aria-label': re.compile(r'Envía la publicación')})
        if share_button and share_button.parent:
            text = share_button.parent.get_text(strip=True)
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])

    def extract_all(self) -> dict:
        """
        Ejecuta todas las extracciones y devuelve un diccionario completo.
        """
        return {
            "author": self.extract_author(),
            # "timestamp": self.extract_timestamp(),
            "message": self.extract_message(),
            # "images": self.extract_images(),
            # "reactions": self.extract_reactions(),
            # "comments": self.extract_comments_count(),
            # "shares": self.extract_shares_count(),
        }


class PostParsedEvent(Event):
    post_data: dict


class AnalyzerResponseEvent(StopEvent):
    is_relevant: bool
    justification: Optional[str]
    promotional_message: Optional[str]


class FacebookPostAnalyzerOutputFormat(BaseModel):
    is_relevant: bool = Field(description="Indica si el mensaje está relacionado con el servicio")
    justification: str = Field(description="Breve explicación de por qué es o no relevante")
    promotional_message: Optional[str] = Field(
        description="Mensaje de respuesta sugerido si es relevante, null en caso contrario")


class FacebookPostAnalyzerAgent(Workflow):
    agent_prompt = """"
Eres Pavel, especialista en automatización de marketing. Tu teléfono de contacto es **+50735591** y debes incluirlo SIEMPRE en el mensaje promocional.

Te voy a dar un mensaje publicado en Facebook. Tu tarea es analizarlo y generar una salida en JSON con tres campos:

- `is_relevant`: booleano. `true` si el mensaje contiene **cualquier intención comercial**, incluyendo:
  * Venta de productos (ej. teléfonos, electrodomésticos, ropa, comida, etc.)
  * Promoción de servicios (ej. reparaciones, clases, asesorías)
  * Ofertas, liquidaciones, descuentos
  * Personas buscando compradores para artículos nuevos o usados
  * Negocios promocionando sus productos
  * Cualquier frase como "vendo", "se vende", "oferta", "aprovecha", "promoción", "remate", "liquidación"
  * Personas que claramente tienen un negocio o emprendimiento aunque no digan "vendo" explícitamente

  `false` solo si el mensaje está vacío, es nulo, o es completamente personal sin relación con ventas (ej. "feliz cumpleaños", "qué opinan de...", temas políticos, familiares, etc.)

- `justification`: texto corto explicando por qué es relevante o no. Si es relevante, menciona qué producto/servicio detectaste.

- `promotional_message`: tu respuesta al autor.  
  * **Si `is_relevant` es `true`**, redacta un mensaje personalizado que:
    1. Salude al autor (si puedes extraer el nombre, úsalo; si no, "Hola").
    2. Mencione específicamente lo que está vendiendo (ej. "veo que estás vendiendo un teléfono").
    3. Conecte con el problema: publicar anuncios uno por uno es tedioso, requiere estar pendiente y sin conocimientos de marketing se pierden ventas.
    4. Ofrezca tu sistema automatizado: él se olvida de publicar, tú te encargas de todo (publicaciones, anuncios, segmentación) y le entregas indicadores de resultados.
    5. Destaque que con tu sistema sus anuncios llegan a más personas interesadas, sin que él tenga que esforzarse.
    6. Termine con invitación a conversar y tu teléfono.
  * **Si `is_relevant` es `false`**, escribe un mensaje amigable ofreciendo tus servicios de forma general: "Si tienes un negocio o vendes algo, yo puedo ayudarte a automatizar tus publicaciones y aumentar ventas sin esfuerzo. Llámame al 50735591. Saludos, Pavel."

**Reglas de comunicación importantes (aplica en el mensaje promocional):**
- Habla de la **incomodidad de publicar a diario** o de hacerlo sin un conocimiento sólido de marketing, lo que genera estrés y malos resultados.
- Resalta la **ventaja de que tu sistema lo haga por ellos**, eliminando esa carga y aportando **indicadores claros** (alcance, interacciones, conversiones) para que el cliente vea el progreso.
- Usa un tono empático y profesional, mostrando que entiendes sus dificultades y que tienes la solución.
- No inventes cosas al mensaje del publicador, si no es claro en lo que vende el mensaje promocional debe ser generico pero con la intención de cambiale los habitos.

**Importante:** Devuelve solo el JSON, sin texto adicional, sin comillas triples ni etiquetas. Ejemplo de formato:

{
  "is_relevant": true,
  "justification": "El usuario está vendiendo ropa",
  "promotional_message": "Hola [nombre], veo que estás promocionando ropa. Publicar a diario puede ser agotador, sobre todo si no tienes experiencia en marketing. Por eso, te propongo algo: yo tengo un sistema automatizado que se encarga de todo por ti. Publica, optimiza y te entrega indicadores claros de resultados. Así te olvidas del estrés y te concentras en tu negocio, mientras yo te ayudo a vender más. ¿Qué te parece si conversamos? Puedes llamarme al +53 50735591 o escribirme. Saludos, Pavel."
}

Nombre del publicador: {facebook_profile}
Mensaje a analizar: {facebook_post}


Entiendo el problema. Tu IA está siendo demasiado restrictiva. Voy a ajustar el prompt para que reconozca **cualquier anuncio de venta** como relevante, aunque no mencione explícitamente necesidades de marketing. Aquí tienes la versión mejorada:

"""

    def __init__(self, lead_description=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.llm = Ollama(
            model='llama3.2:3b',
            base_url='https://ia.pavelcode5426.duckdns.org',
            context_window=50_000,
            request_timeout=1500, json_mode=True)

        self.lead_description = lead_description

    @step
    def start_workflow(self, ev: StartEvent) -> PostParsedEvent:
        raw_html = ev.get('raw_html', "")
        post_data = FacebookPostExtractor(raw_html).extract_all()
        return PostParsedEvent(post_data=post_data)

    @step
    async def make_decision(self, ev: PostParsedEvent) -> AnalyzerResponseEvent:
        post_data = ev.post_data
        output_parser = PydanticOutputParser(FacebookPostAnalyzerOutputFormat)
        template_prompt = PromptTemplate(self.agent_prompt, output_parser=output_parser)

        facebook_profile = post_data.get('author').get('name')
        facebook_post = post_data.get('message')
        print(f"Generando mensaje para: {facebook_post}")

        if not facebook_post:
            return AnalyzerResponseEvent(is_relevant=False, justification=None, promotional_message=None)

        response = self.llm.predict(template_prompt, facebook_post=facebook_post, facebook_profile=facebook_profile)
        result = output_parser.parse(response)
        return AnalyzerResponseEvent(
            is_relevant=result.is_relevant,
            justification=result.justification,
            promotional_message=result.promotional_message
        )
