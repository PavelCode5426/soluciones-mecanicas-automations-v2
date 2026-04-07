import asyncio
import re
from typing import Optional

import nest_asyncio
from bs4 import BeautifulSoup
from huggingface_hub import InferenceClient
from llama_index.core import PromptTemplate
from llama_index.core.workflow import Workflow, Event, step, StartEvent, StopEvent
from llama_index.llms.ollama import Ollama
from pydantic import BaseModel, Field, HttpUrl


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
    whatsapp_promotional_message: Optional[str]


class FacebookPostAnalyzerOutputFormat(BaseModel):
    is_relevant: bool = Field(description="Indica si el mensaje está relacionado con el servicio")
    justification: str = Field(description="Breve explicación de por qué es o no relevante")
    phone_number: Optional[str] = Field(description="Numero de telefono para contactar, null en caso contrario")
    product_service: Optional[str] = Field(description="Describe lo que vende o el servicio que se brinda")


class FacebookPostAnalyzerAgent(Workflow):
    classificator_prompt = """
    Eres un experto en prospección de ventas. Tu misión es analizar posts de Facebook para identificar vendedores potenciales.

    POST A ANALIZAR:
    - Autor: {facebook_profile}
    - Contenido: {facebook_post}

    REGLAS DE CLASIFICACIÓN:
    1. `is_relevant`: Debe ser true SOLO si el autor está vendiendo un producto o servicio. Si el autor está BUSCANDO comprar algo o hace una pregunta informativa, marca false.
    2. `justification`: Una frase corta. Ej: "Vende repuestos de autos" o "Es una consulta sobre clima, no relevante".
    3. `phone_number`: Extrae solo números. Si hay varios, el primero. Si no hay, null. Ignora precios (ej. $100).
    4. `product_service`: Identifica qué vende. Ej: "Zapatos artesanales", "Servicios de mudanza". Máximo 5 palabras.

    RESPONDE ÚNICAMENTE EN FORMATO JSON:
    {{
      "is_relevant": boolean,
      "justification": "string",
      "phone_number": "string o null",
      "product_service": "string o null"
    }}
    """

    agent_prompt = """
    Eres Pavel, un estratega de conversión. Tu objetivo es dejar un comentario en Facebook que cuestione la eficiencia del vendedor y lo obligue a buscar profesionalismo.

    DATOS:
    - Nombre: {facebook_profile}
    - Producto: {product_service}
    - Link: {whatsapp_link}

    ESTRUCTURA OBLIGATORIA:
    1. GOLPE DE REALIDAD: "Hola {facebook_profile}, tienes un producto con potencial, pero publicarlo así es jugar a la lotería."
    2. EL DIAGNÓSTICO: "Mientras tu gestión dependa de responder comentarios manualmente, tu negocio tiene un techo de cristal que no te deja escalar."
    3. LA DIFERENCIA: "Yo instalo infraestructuras de conversión que venden 24/7 sin que tú muevas un dedo."
    4. LA PREGUNTA DISRUPTIVA: "¿Quieres un negocio real o un hobby agotador?"
    5. CTA: "Hablemos aquí: {whatsapp_link} — Pavel de Sinergia Solutions."

    REGLAS CRÍTICAS:
    - Una sola línea (sin saltos de línea).
    - Máximo 600 caracteres.
    - Tono: Desafiante, experto, de alto nivel.
    - NO uses emojis.
    - Si el nombre es "sin nombre", usa "Hola,".
    """

    def __init__(self, lead_description=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.llm = Ollama(model='llama3.2:3b', base_url='https://ia.pavelcode5426.duckdns.org', context_window=20_000,
                          request_timeout=500)
        self.lead_description = lead_description

    @step
    def start_workflow(self, ev: StartEvent) -> PostParsedEvent:
        raw_html = ev.get('raw_html', "")
        post_data = FacebookPostExtractor(raw_html).extract_all()
        return PostParsedEvent(post_data=post_data)

    @step
    async def make_decision(self, ev: PostParsedEvent) -> AnalyzerResponseEvent:
        post_data = ev.post_data
        facebook_profile = post_data.get('author').get('name')
        facebook_post = post_data.get('message')
        print(f"Generando mensaje para: {facebook_post}")

        if not facebook_post:
            return AnalyzerResponseEvent(is_relevant=False, justification=None, promotional_message=None)

        response = self.llm.structured_predict(FacebookPostAnalyzerOutputFormat,
                                               PromptTemplate(self.classificator_prompt),
                                               facebook_post=facebook_post, facebook_profile=facebook_profile)

        facebook_promotional_message = None
        if response.is_relevant:
            whatsapp_link = "https://wa.me/50735591?text=Hola"
            facebook_promotional_message = self.llm.predict(
                PromptTemplate(self.agent_prompt),
                whatsapp_link=whatsapp_link,
                facebook_post=facebook_post,
                facebook_profile=facebook_profile,
                product_service=response.product_service,
                extracted_phone=response.phone_number
            )

        return AnalyzerResponseEvent(is_relevant=response.is_relevant, justification=response.justification,
                                     promotional_message=facebook_promotional_message)


class FacebookPossibleFriend(BaseModel):
    """Modelo para representar un posible amigo en Facebook"""
    profile_url: HttpUrl = Field(description="URL completa del perfil de usuario de Facebook")
    avatar: HttpUrl = Field(description="URL de la imagen de perfil del usuario")
    name: str = Field(description="Nombre completo del usuario mostrado en el perfil", min_length=1)
    common_friends: Optional[int] = Field(description="Número de amigos en común con el usuario actual", ge=0)


class FacebookAccountAgent:
    llm: Ollama
    inference_client: InferenceClient

    def __init__(self, llm: Ollama, inference_client) -> None:
        self.llm = llm
        self.inference_client = inference_client

    def could_be_friend(self, html_content):
        promp_template = PromptTemplate(
            """
           Extract information about a Facebook possible friend from the following HTML content.
           HTML:
           {html_content}
            """
        )

        info = self.llm.structured_predict(FacebookPossibleFriend, promp_template, html_content=html_content)
        is_nsfw = self.is_nsfw_image(info.avatar)
        return info

    def is_nsfw_image(self, image) -> bool:
        output = self.inference_client.image_classification(image, model="Falconsai/nsfw_image_detection")[0]
        return output.label == 'normal' and output.score > 0.85
