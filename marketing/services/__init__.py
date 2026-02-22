from pathlib import Path

import requests
from django.conf import settings
from llama_index.core import Settings, StorageContext, load_index_from_storage, VectorStoreIndex, Document, \
    SimpleDirectoryReader
from llama_index.core.agent import FunctionAgent, ReActAgent
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.tools import QueryEngineTool, FunctionTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

import marketing.ia_tools as ia_tools
from marketing.models import FacebookPost


class IAService:
    system_prompt = """
    Eres Emily, una vendedora amable y profesional de Soluciones Hevia, una tienda de autopartes y piezas de autos.

    INFORMACIÓN DE LA TIENDA:
    - Nombre: Soluciones Hevia
    - Sitio web: www.solucioneshevia.com
    - Teléfono: +53 54266836
    - Dirección: Santa Emilia 210 e/ Flores y Serrano
    - Contacto: Ing. Michael Hevia Rodriguez

    INSTRUCCIONES:
    1. Responde SIEMPRE en español, de forma cordial y servicial.
    2. Cuando el cliente te salude (hola, buenos días, etc.), responde amablemente y ofrécele ayuda, ten en cuenta que debes presentarte si no lo haz hecho.
    3. Si el cliente pide información de la tienda (dirección, teléfono), puedes proporcionarla directamente.
    4. Mantén un tono positivo y orientado a soluciones.
    
    IMPORTANTE: Siempre que el cliente pregunte por productos, precios, disponibilidad o categorías, 
    DEBES utilizar las herramientas disponibles ('consultar_productos' y 'consultar_categorias_de_productos') para obtener la información.
    No inventes productos ni uses tu conocimiento interno para responder sobre el catálogo. 
    Si no estás seguro de qué herramienta usar, prefiere llamar a la función correspondiente antes de responder."
    
    """

    verbose = True
    embedding_model = 'nomic-embed-text:latest'
    llm_model = 'llama3.1:8b-instruct-q4_K_M'

    def init_llamaindex(self):
        host = "https://ia.pavelcode5426.duckdns.org"  # settings.IA_OLLAMA_HOST
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

    def get_products_query_engine_tool_____no_usar(self, reset=False):
        PERSIST_DIR = settings.IA_POST_PERSISTEN / "products"
        if PERSIST_DIR.exists() and not reset:
            storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
            vector_index = load_index_from_storage(storage_context)
        else:
            DATA_DIR = Path(__file__).parent / 'data/products'
            documents = SimpleDirectoryReader(DATA_DIR).load_data()
            # parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
            # nodes = parser.get_nodes_from_documents(documents)
            # vector_index = VectorStoreIndex(nodes)
            vector_index = VectorStoreIndex.from_documents(documents)
            vector_index.storage_context.persist(PERSIST_DIR)

        query_engine = vector_index.as_query_engine(response_mode=ResponseMode.COMPACT, use_async=True,
                                                    similarity_top_k=10)
        return QueryEngineTool.from_defaults(
            query_engine=query_engine,
            name="consultar_precios",
            description="Utiliza esta herramienta para obtener información sobre productos y precios. Pasa la consulta del cliente tal cual."
        )

    def get_products_function_tool(self):
        return FunctionTool.from_defaults(
            ia_tools.get_products_information,
            name="consultar_productos",
            description="""
            "Utiliza esta función para obtener información detallada (precio, disponibilidad, descripción) de uno o varios productos de la tienda. 
            La función devuelve una lista de productos relevantes, puedes pasar por parametros lo que esta buscando el cliente, asegurate de pasarlo en singular para poder encontrar el producto
            No la uses para preguntar sobre categorías; para eso está 'consultar_categorias_de_productos'."
            """)

    def get_categories_function_tool(self):
        return FunctionTool.from_defaults(
            ia_tools.get_categories_information,
            name="consultar_categorias_de_productos",
            description="Útil cuando el cliente pregunta por los tipos de productos que comercializamos. Debes analizar la respuesta para adaptarla a la necesidad del cliente.")

    def get_seller_agent(self):
        self.init_llamaindex()
        products_tool = self.get_products_function_tool()
        categories_tool = self.get_categories_function_tool()

        return FunctionAgent(name='seller_agent',
                             verbose=self.verbose,
                             description="Encagado de responder informacion de la tienda y productos.",
                             tools=[products_tool, categories_tool], system_prompt=self.system_prompt)

    def get_seller_agent_thinker(self):
        self.init_llamaindex()
        products_tool = self.get_products_function_tool()

        return ReActAgent(name='seller_agent',
                          verbose=self.verbose,
                          description="Encagado de responder informacion de la tienda y productos.",
                          tools=[products_tool], system_prompt=self.system_prompt)


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


class SolucionesMecanicasAPIServices:
    _initialized = False
    _api_url = None

    @classmethod
    def __ensure_initialized(cls):
        if not cls._initialized:
            cls._api_url = 'https://api.solucioneshevia.com'
            cls._initialized = True

    @classmethod
    def get_all_products(cls, search: str) -> list:
        cls.__ensure_initialized()
        response = requests.get(f'{cls._api_url}/core/shops', params=dict(search=search.lower()))
        response.raise_for_status()
        response = response.json()
        all_products = [*response.get('results')]
        while response.get('next'):
            response = requests.get(response.get('next')).json()
            all_products.extend(response.get('results'))
        return all_products

    @classmethod
    def get_all_categories(cls) -> list:
        cls.__ensure_initialized()
        response = requests.get(f'{cls._api_url}/core/categories-with-products/')
        response.raise_for_status()
        return response.json()
