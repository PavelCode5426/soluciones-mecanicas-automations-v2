import random
import time
from pathlib import Path

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import F
from django.utils.timezone import now
from llama_index.core import Settings, StorageContext, load_index_from_storage, VectorStoreIndex, Document, \
    SimpleDirectoryReader
from llama_index.core.agent import FunctionAgent
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from playwright.sync_api import sync_playwright, PlaywrightContextManager, Playwright

from facebook.models import FacebookPost
from facebook.models import FacebookProfile, FacebookGroup


def get_playwright() -> PlaywrightContextManager:
    return sync_playwright()


class FacebookAutomationService:
    def __init__(self, user: FacebookProfile):
        self.user = user

    def check_status(self):
        self.refresh_user()
        if self.user.active:
            with (get_playwright() as pw):
                browser = self.get_browser(pw)
                page = browser.new_page()
                page.goto('https://www.facebook.com/')
                self.user.active = not bool(page.locator('text=Iniciar sesión').count())
        self.user.save(update_fields=['active'])
        return self.user.active

    def refresh_user(self):
        self.user.refresh_from_db()

    def get_browser(self, pw: Playwright):
        context = pw.chromium.launch(**settings.PLAYWRIGHT).new_context(storage_state=self.user.context)
        context.set_default_timeout(settings.PLAYWRIGHT['timeout'])
        return context

    def get_all_groups(self):
        self.refresh_user()
        with get_playwright() as pw:
            browser = self.get_browser(pw)
            page = browser.new_page()
            page.goto("https://www.facebook.com/groups/joins/?nav_source=tab", timeout=settings.PLAYWRIGHT['timeout'])

            last_height = page.evaluate("document.body.scrollHeight")
            while True:
                page.evaluate(f"window.scrollBy(0,document.body.scrollHeight)")
                time.sleep(20)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            groups_links = page.locator('[role="main"] [role="list"] [role="listitem"] a') \
                .filter(has_not_text='Ver grupo')

            groups = []
            for link in groups_links.all():
                if link.text_content():
                    groups.append(dict(
                        url=link.get_attribute('href'),
                        name=link.text_content()
                    ))
            page.close()
            return groups

    def create_post(self, group: FacebookGroup, post: FacebookPost):
        self.refresh_user()
        group.refresh_from_db()
        post.refresh_from_db()
        if post.active and group.active and self.user.active:
            screenshot, exception = self.__publish_group_post(group.url, post)
            file_name = f"{group}_screenshot.jpeg".lower()
            group.screenshot.delete(False)
            group.screenshot.save(file_name, ContentFile(screenshot), False)

            group.error_at = None
            if exception:
                group.error_at = now()
                group.save()
                raise exception

            group.save()
            post.published_count = F('published_count') + 1
            post.save()

    def __publish_group_post(self, url, post: FacebookPost) -> (bytes, Exception | None):
        exception = None
        with (get_playwright() as pw):
            try:
                browser = self.get_browser(pw)
                page = browser.new_page()
                page.goto(url)

                # page.get_by_text('Escribe algo').click(timeout=settings.PLAYWRIGHT['timeout'])
                # page.get_by_role('textbox').click(timeout=settings.PLAYWRIGHT['timeout'])
                # file_input = page.locator('input[type="file"][multiple]')
                # file_input.set_input_files(files=[post.file.path])
                # page.keyboard.type(post.text)
                # page.get_by_text('Publicar').click()
                # page.get_by_text("Publicando").wait_for(state='hidden')

                page.wait_for_load_state(state='load')
                write_btn = page.get_by_text('Escribe algo')
                write_btn.wait_for(state='visible')
                write_btn.click()

                # page.get_by_text('Crear publicación').wait_for(state='visible')
                text_area = page.locator('[aria-placeholder*="Crea una publicación"]')
                # text_area.wait_for(state='visible')
                text_area.click()

                if post.file:
                    file_input = page.locator('input[type="file"][multiple]')
                    file_input.set_input_files(files=[post.file.path])

                # page.keyboard.type(post.text)
                page.keyboard.insert_text(post.text)
                page.keyboard.insert_text(self.user.posts_footer)
                time.sleep(random.randint(30, 60))

                page.click('[aria-label="Publicar"]')
                page.locator('span', has_text='Publicando').wait_for(state='hidden')
                # page.get_by_text("Publicando").wait_for(state='hidden')

            except Exception as e:
                exception = e
            return page.screenshot(quality=80, type='jpeg'), exception

    def sign_in(self, user: FacebookProfile):
        pass


class IAService:
    system_prompt = """
    Eres Emily, una vendedora amable y profesional de Soluciones Hevia, una tienda de autopartes y piezas de autos.

    INFORMACIÓN DE LA TIENDA:
    - Nombre: Soluciones Hevia
    - Web: www.solucioneshevia.com
    - Teléfono: +53 54266836
    - Dirección: Santa Emilia 210 e/ Flores y Serrano
    - Contacto: Ing. Michael Hevia Rodriguez

    INSTRUCCIONES:
    1. Responde SIEMPRE en español, de forma cordial y servicial.
    2. Cuando el cliente te salude (hola, buenos días, etc.), responde amablemente y ofrécele ayuda.
    3. Para cualquier consulta sobre productos, precios o disponibilidad, DEBES usar la herramienta 'consultar_productos' (o el nombre que le hayas dado). Nunca inventes información.
    4. Si el cliente pide información de la tienda (dirección, teléfono), puedes proporcionarla directamente.
    5. Mantén un tono positivo y orientado a soluciones.
    6. Solo usa la herramienta 'consultar_productos' cuando el cliente pregunte por productos, precios o disponibilidad.

    Ejemplo de respuesta a saludo:
    Cliente: "Hola"
    Emily: "¡Hola! Soy Emily de Soluciones Hevia. ¿En qué puedo ayudarte hoy? Tenemos una amplia variedad de autopartes y herramientas. ¿Buscas algún producto en especial?"
    """

    verbose = True
    embedding_model = 'nomic-embed-text:latest'
    llm_model = 'llama3.1:8b-instruct-q4_K_M'

    def init_llamaindex(self):
        host = settings.IA_OLLAMA_HOST
        Settings.embed_model = OllamaEmbedding(model_name=self.embedding_model, base_url=host)
        Settings.llm = Ollama(base_url=host, model=self.llm_model, request_timeout=360.0,
                              context_window=8000, temperature=0.0)

    def get_facebook_post_query_engine_tool(self, reset=False):
        PERSIST_DIR = settings.IA_POST_PERSISTEN / "post"
        if PERSIST_DIR.exists() and not reset:
            storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
            vector_index = load_index_from_storage(storage_context)
        else:
            documents = []
            posts = FacebookPost.objects.filter(active=True).all()
            for post in posts:
                documents.append(Document(text=post.text))
            vector_index = VectorStoreIndex.from_documents(documents)
            vector_index.storage_context.persist(PERSIST_DIR)

        query_engine = vector_index.as_query_engine(response_mode=ResponseMode.COMPACT, use_async=True)
        return QueryEngineTool.from_defaults(
            query_engine=query_engine,
            name="consultar_precios",
            description="Utiliza esta herramienta para obtener información sobre productos y precios. Pasa la consulta del cliente tal cual."
        )

    def get_products_query_engine_tool(self, reset=False):
        PERSIST_DIR = settings.IA_POST_PERSISTEN / "products"
        if PERSIST_DIR.exists() and not reset:
            storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
            vector_index = load_index_from_storage(storage_context)
        else:
            DATA_DIR = Path(__file__).parent / 'data/products'
            documents = SimpleDirectoryReader(DATA_DIR).load_data()
            parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
            nodes = parser.get_nodes_from_documents(documents)
            vector_index = VectorStoreIndex(nodes)
            # vector_index = VectorStoreIndex.from_documents(documents)
            vector_index.storage_context.persist(PERSIST_DIR)

        query_engine = vector_index.as_query_engine(response_mode=ResponseMode.COMPACT, use_async=True,
                                                    similarity_top_k=10)
        return QueryEngineTool.from_defaults(
            query_engine=query_engine,
            name="consultar_precios",
            description="Utiliza esta herramienta para obtener información sobre productos y precios. Pasa la consulta del cliente tal cual."
        )

    def get_seller_agent(self):
        self.init_llamaindex()
        products_query_engine_tool = self.get_products_query_engine_tool()

        return FunctionAgent(name='seller_agent',
                             verbose=self.verbose,
                             description="Encagado de responder informacion de la tienda y productos.",
                             tools=[products_query_engine_tool], system_prompt=self.system_prompt)

    def get_seller_agent_thinker(self):
        self.init_llamaindex()
        products_query_engine_tool = self.get_products_query_engine_tool()

        return FunctionAgent(name='seller_agent',
                             verbose=self.verbose,
                             description="Encagado de responder informacion de la tienda y productos.",
                             tools=[products_query_engine_tool], system_prompt=self.system_prompt)


class WAHAService:
    """
    Wrapper para la API WAHA, envia mensajes via WhatsApp

    Raises:
        ConfigurationDoesNotExistException: No existe el archivo de configuración
        ErrorContactingMessagingAPIException: Problemas al contactar la API WAHA

    Returns:
        _type_: _description_
    """

    _initialized = False
    _auth = None
    _api_url = None

    @classmethod
    def _ensure_initialized(cls):
        if not cls._initialized:
            cls._auth = ('pavelcode5426', 'pavelcode5426')
            cls._headers = {'X-Api-Key': 'admin'}
            cls._api_url = 'https://whatsapp.pavelcode5426.duckdns.org'
            cls._initialized = True

    @staticmethod
    def check_exist(phone_number: str) -> dict:
        """
        Verifica si el número telefónico está registrado en WhatsApp

        Args:
            phone_number (str): Número telefónico del cliente

        Returns:
            bool: True | False
        """
        WAHAService._ensure_initialized()
        response = requests.get(
            f"{WAHAService._api_url}/api/contacts/check-exists",
            headers=WAHAService._headers,
            auth=WAHAService._auth,
            params={"phone": phone_number, "session": "default"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def start_typing(chat_id: str) -> int:
        """
        WhatsApp comienzo de escritura

        Args:
            phone_number (str): Número telefónico del cliente

        Returns:
            int: HTTP código de estado
        """
        WAHAService._ensure_initialized()
        response = requests.post(
            f"{WAHAService._api_url}/api/startTyping",
            auth=WAHAService._auth,
            headers=WAHAService._headers,
            data={"chatId": chat_id, "session": "default"},
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code

    @staticmethod
    def stop_typing(chat_id: str) -> int:
        """
        WhatsApp detener la escrituea

        Args:
            phone_number (str): Número telefónico del cliente

        Returns:
            int: HTTP código de estado
        """
        WAHAService._ensure_initialized()
        response = requests.post(
            f"{WAHAService._api_url}/api/stopTyping",
            auth=WAHAService._auth,
            headers=WAHAService._headers,
            data={"chatId": chat_id, "session": "default"},
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code

    @staticmethod
    def send_text(chat_id: str, message: str) -> int:
        """
        WhatsApp envío de mensaje
        Args:
            phone_number (str): Número telefónico del cliente
            message (str): Mensaje a enviar

        Returns:
            int: HTTP código de estado
        """
        WAHAService._ensure_initialized()

        response = requests.post(
            f"{WAHAService._api_url}/api/sendText",
            headers=WAHAService._headers,
            auth=WAHAService._auth,
            json={
                "chatId": chat_id,
                "reply_to": None,
                "text": message,
                "linkPreview": True,
                "session": "default",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code

    @staticmethod
    def send_image(chat_id: str, image_url: str, caption: str) -> int:
        """
        WhatsApp enviar imagen

        Args:
            phone_number (str): Número telefónico del cliente
            image_url (str): Imagen a enviar
            caption (str): Texto que acompaña a la imagen
        Returns:
            int: HTTP código de estado
        """

        WAHAService._ensure_initialized()

        response = requests.post(
            f"{WAHAService._api_url}/api/sendImage",
            headers=WAHAService._headers,
            auth=WAHAService._auth,
            data={
                "chatId": chat_id,
                "image": image_url,
                "caption": caption,
                "session": "default",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code
