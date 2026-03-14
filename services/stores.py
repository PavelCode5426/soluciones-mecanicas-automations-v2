import requests


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
