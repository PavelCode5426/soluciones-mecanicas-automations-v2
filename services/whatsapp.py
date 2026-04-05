import requests


class WAHAService:
    def __init__(self, server_url: str, session: str = "default", api_key=None, username=None, password=None):
        self._session = session
        self._auth = None
        self._api_url = server_url
        self._headers = {'X-Api-Key': api_key}
        if username and password:
            self._auth = (username, password)

    def __get_session_config(self, webhook_url: str = None):
        data = {"gows": {"storage": {"messages": False, "groups": False, "chats": False, "labels": False}}}
        if webhook_url:
            data.setdefault('webhooks', [{
                "url": webhook_url,
                "events": ["message", "session.status"],
                "retries": {
                    "delaySeconds": 2,
                    "attempts": 5,
                    "policy": "linear"
                }
            }])

        return data

    def create_session(self, webhook_url=None):
        data = {"name": self._session, "config": self.__get_session_config(webhook_url)}
        response = requests.post(f"{self._api_url}/api/sessions", headers=self._headers, auth=self._auth, json=data)
        response.raise_for_status()
        return response.json()

    def update_session(self, webhook_url: str = None):
        data = {"name": self._session, "config": self.__get_session_config(webhook_url)}
        response = requests.put(f"{self._api_url}/api/sessions/{self._session}", headers=self._headers,
                                auth=self._auth, json=data)
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
        )
        response.raise_for_status()
        return response.json()

    def start_typing(self, chat_id: str) -> int:
        response = requests.post(
            f"{self._api_url}/api/startTyping",
            auth=self._auth,
            headers=self._headers,
            data={"chatId": chat_id, "session": self._session},
        )
        response.raise_for_status()
        return response.status_code

    def stop_typing(self, chat_id: str) -> int:
        response = requests.post(
            f"{self._api_url}/api/stopTyping",
            auth=self._auth,
            headers=self._headers,
            data={"chatId": chat_id, "session": self._session},
        )
        response.raise_for_status()
        return response.status_code

    def set_chat_presence(self, chat_id: str, presence: str) -> int:
        response = requests.post(
            f"{self._api_url}/api/{self._session}/presence",
            auth=self._auth,
            headers=self._headers,
            data={"chatId": chat_id, "presence": presence, "session": self._session}
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
        return response.json()

    def create_video_status(self, data):
        response = requests.post(
            f'{self._api_url}/api/{self._session}/status/video',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response.json()

    def create_voice_status(self, data):
        response = requests.post(
            f'{self._api_url}/api/{self._session}/status/voice',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response.json()

    def create_image_status(self, data):
        response = requests.post(
            f'{self._api_url}/api/{self._session}/status/image',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response.json()

    def send_list_message(self, data: dict):
        data.setdefault('session', self._session)
        print(data)
        response = requests.post(
            f'{self._api_url}/api/sendList',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response.json()

    def send_text_message(self, data: dict):
        data.setdefault('session', self._session)
        response = requests.post(
            f'{self._api_url}/api/sendText',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response.json()

    def send_video_message(self, data: dict):
        data.setdefault('session', self._session)
        response = requests.post(
            f'{self._api_url}/api/sendVideo',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response.json()

    def send_voice_message(self, data: dict):
        data.setdefault('session', self._session)
        response = requests.post(
            f'{self._api_url}/api/sendVoice',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response.json()

    def send_image_message(self, data: dict):
        data.setdefault('session', self._session)
        response = requests.post(
            f'{self._api_url}/api/sendImage',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response.json()

    def send_file_message(self, data: dict):
        data.setdefault('session', self._session)
        response = requests.post(
            f'{self._api_url}/api/sendFile',
            headers=self._headers, auth=self._auth, json=data
        )
        response.raise_for_status()
        return response.json()

    def forward_message(self, chat_id: str, message_id: str):
        response = requests.post(
            f'{self._api_url}/api/forwardMessage',
            headers=self._headers, auth=self._auth, data={
                "session": self._session, "chatId": chat_id, "messageId": message_id
            }
        )
        response.raise_for_status()
        return response.json()

    def chat_messages(self, chat_id: str, filters: dict):
        filters.setdefault('limit', 10)
        filters.setdefault('downloadMedia', False)
        filters.setdefault('merge', True)
        filters.setdefault('sortOrder', 'asc')
        filters.setdefault('sortBy', 'timestamp')

        response = requests.get(
            f"{self._api_url}/api/{self._session}/chats/{chat_id}/messages",
            headers=self._headers, auth=self._auth,
            params=filters
        )
        response.raise_for_status()
        return response.json()

    def get_last_message_timestamp(self, chat_id: str):
        messages = self.chat_messages(chat_id, {"limit": 2, 'sortOrder': 'desc'})
        return None if len(messages) == 0 else messages[-1]['timestamp']
