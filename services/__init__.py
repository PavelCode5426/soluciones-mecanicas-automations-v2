import requests


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
