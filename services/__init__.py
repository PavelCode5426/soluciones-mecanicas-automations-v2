import requests
from django.conf import settings

from ia_assistant.models import RAGApplication


class WAHAService:
    """
    Wrapper para la API WAHA, envia mensajes via WhatsApp

    Raises:
        ConfigurationDoesNotExistException: No existe el archivo de configuración
        ErrorContactingMessagingAPIException: Problemas al contactar la API WAHA

    Returns:
        _type_: _description_
    """

    @classmethod
    def initialize_using_rag(cls, rag: RAGApplication):
        return WAHAService(
            server_url=rag.config.get('waha_base_url'),
            server_username=rag.config.get('waha_username'),
            server_password=rag.config.get('waha_password'),
            server_api_key=rag.config.get('waha_api_key'),
        )

    def __init__(self, server_url: str, server_api_key=None, server_username=None, server_password=None):
        self._auth = None
        self._api_url = server_url
        self._headers = {'X-Api-Key': server_api_key}
        if server_username and server_password:
            self._auth = (server_username, server_password)

    def check_exist(self, phone_number: str) -> dict:
        """
        Verifica si el número telefónico está registrado en WhatsApp

        Args:
            phone_number (str): Número telefónico del cliente

        Returns:
            bool: True | False
        """
        response = requests.get(
            f"{self._api_url}/api/contacts/check-exists",
            headers=self._headers,
            auth=self._auth,
            params={"phone": phone_number, "session": "default"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def start_typing(self, chat_id: str) -> int:
        """
        WhatsApp comienzo de escritura

        Args:
            phone_number (str): Número telefónico del cliente

        Returns:
            int: HTTP código de estado
        """
        response = requests.post(
            f"{self._api_url}/api/startTyping",
            auth=self._auth,
            headers=self._headers,
            data={"chatId": chat_id, "session": "default"},
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code

    def stop_typing(self, chat_id: str) -> int:
        """
        WhatsApp detener la escrituea

        Args:
            phone_number (str): Número telefónico del cliente

        Returns:
            int: HTTP código de estado
        """
        response = requests.post(
            f"{self._api_url}/api/stopTyping",
            auth=self._auth,
            headers=self._headers,
            data={"chatId": chat_id, "session": "default"},
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code

    def send_text(self, chat_id: str, message: str) -> int:
        """
        WhatsApp envío de mensaje
        Args:
            phone_number (str): Número telefónico del cliente
            message (str): Mensaje a enviar

        Returns:
            int: HTTP código de estado
        """
        response = requests.post(
            f"{self._api_url}/api/sendText",
            headers=self._headers,
            auth=self._auth,
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

    def send_image(self, chat_id: str, image_url: str, caption: str) -> int:
        """
        WhatsApp enviar imagen

        Args:
            phone_number (str): Número telefónico del cliente
            image_url (str): Imagen a enviar
            caption (str): Texto que acompaña a la imagen
        Returns:
            int: HTTP código de estado
        """

        response = requests.post(
            f"{self._api_url}/api/sendImage",
            headers=self._headers,
            auth=self._auth,
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
    _authorization_token = 'f192f63804abd9c7c32f8621f247c807247c9326'

    @classmethod
    def __ensure_initialized(cls):
        if not cls._initialized:
            cls._api_url = 'https://api.solucioneshevia.com'
            cls._initialized = True

    @classmethod
    def __get_headers(cls):
        return {'Authorization': f'Token {cls._authorization_token}'}

    @classmethod
    def get_all_products(cls, search: str) -> list:
        cls.__ensure_initialized()
        response = requests.get(f'{cls._api_url}/core/shops',
                                params=dict(search=search.lower()),
                                headers=cls.__get_headers())
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
        response = requests.get(f'{cls._api_url}/core/categories-with-products/', headers=cls.__get_headers())
        response.raise_for_status()
        return response.json()
