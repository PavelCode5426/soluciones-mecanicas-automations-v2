import requests


class WAHAService:
    def __init__(self, server_url: str, session: str = "default", api_key=None, username=None, password=None):
        self._session = session
        self._auth = None
        self._api_url = server_url
        self._headers = {'X-Api-Key': api_key}
        if username and password:
            self._auth = (username, password)

    def __get_session_config(self, webhook_url: str):
        return dict(webhooks=[
            {
                "url": webhook_url,
                "events": ["message", "session.status"],
                "retries": {
                    "delaySeconds": 2,
                    "attempts": 5,
                    "policy": "linear"
                }
            }
        ])

    def create_session(self, webhook_url=None):
        response = requests.post(
            f"{self._api_url}/api/sessions", headers=self._headers, auth=self._auth,
            data={"name": self._session, "config": self.__get_session_config()}
        )
        response.raise_for_status()
        return response.json()

    def update_session(self, webhook_url: str = None):
        data = {"name": self._session}
        if webhook_url:
            data.setdefault("config", self.__get_session_config(webhook_url))

        response = requests.put(
            f"{self._api_url}/api/sessions/{self._session}", headers=self._headers, auth=self._auth, data=data)
        response.raise_for_status()
        return response.json()

    def get_profile_info(self):
        response = requests.get(
            f"{self._api_url}/api/{self._session}/profile",
            headers=self._headers, auth=self._auth,
        )
        response.raise_for_status()
        return response.json()

    def check_exist(self, phone_number: str) -> dict:
        response = requests.get(
            f"{self._api_url}/api/contacts/check-exists",
            headers=self._headers,
            auth=self._auth,
            params={"phone": phone_number, "session": self._session},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def start_typing(self, chat_id: str) -> int:
        response = requests.post(
            f"{self._api_url}/api/startTyping",
            auth=self._auth,
            headers=self._headers,
            data={"chatId": chat_id, "session": self._session},
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code

    def stop_typing(self, chat_id: str) -> int:
        response = requests.post(
            f"{self._api_url}/api/stopTyping",
            auth=self._auth,
            headers=self._headers,
            data={"chatId": chat_id, "session": self._session},
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code

    def send_text(self, chat_id: str, message: str) -> int:
        response = requests.post(
            f"{self._api_url}/api/sendText",
            headers=self._headers,
            auth=self._auth,
            json={
                "chatId": chat_id,
                "reply_to": None,
                "text": message,
                "linkPreview": True,
                "session": self._session,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code

    def send_image(self, chat_id: str, image_url: str, caption: str) -> int:
        response = requests.post(
            f"{self._api_url}/api/sendImage",
            headers=self._headers, auth=self._auth,
            data={
                "chatId": chat_id,
                "image": image_url,
                "caption": caption,
                "session": self._session,
            },
        )
        response.raise_for_status()
        return response.status_code

    def get_all_groups(self):
        response = requests.get(
            f"{self._api_url}/api/{self._session}/groups",
            headers=self._headers, auth=self._auth,
            params={"exclude": ['participants']}
        )
        response.raise_for_status()
        return response.json()

    def get_all_contacts(self):
        response = requests.get(
            f"{self._api_url}/api/contacts/all",
            headers=self._headers, auth=self._auth,
            params={"session": self._session}
        )
        response.raise_for_status()
        return response.json()

    def refresh_groups(self):
        response = requests.post(
            f"{self._api_url}/api/{self._session}/groups/refresh",
            headers=self._headers, auth=self._auth,
        )
        response.raise_for_status()

    def get_group_participants(self, group_id):
        response = requests.get(
            f"{self._api_url}/api/{self._session}/groups/{group_id}/participants",
            headers=self._headers, auth=self._auth,
        )
        response.raise_for_status()
        return response.json()

    def create_text_status(self, data):
        response = requests.post(
            f'{self._api_url}/api/{self._session}/status/text/',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response

    def create_video_status(self, data):
        response = requests.post(
            f'{self._api_url}/api/{self._session}/status/video',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response

    def create_voice_status(self, data):
        response = requests.post(
            f'{self._api_url}/api/{self._session}/status/voice',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response

    def create_image_status(self, data):
        response = requests.post(
            f'{self._api_url}/api/{self._session}/status/image',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response
