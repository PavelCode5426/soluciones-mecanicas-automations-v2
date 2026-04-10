import asyncio
import mimetypes
import os
import threading

from django.core.cache import cache

from services.whatsapp import WAHAService


def get_file_mimetype(file):
    """
    Detecta el MIME type del archivo usando mimetypes
    """
    try:
        file_name = file.name
        extension = os.path.splitext(file_name)[1].lower()

        mimetype, encoding = mimetypes.guess_type(file_name)

        if not mimetype:
            mime_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp',
                '.svg': 'image/svg+xml',
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska',
                '.webm': 'video/webm',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.ogg': 'audio/ogg',
                '.m4a': 'audio/mp4',
                '.flac': 'audio/flac',
                '.pdf': 'application/pdf',
                '.txt': 'text/plain',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            }
            mimetype = mime_map.get(extension, 'application/octet-stream')

        return mimetype
    except Exception as e:
        return 'application/octet-stream'


def get_message_type(file):
    minetype = get_file_mimetype(file).split('/')[0]
    if minetype in ['application']:
        return 'file'
    return minetype


def keep_presence_loop_task(service: WAHAService, chat_id, presence):
    async def __keep_typing():
        try:
            while True:
                service.set_chat_presence(chat_id, presence)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            service.set_chat_presence(chat_id, "paused")

    return asyncio.create_task(__keep_typing())


class ChatMessageDebouncer:

    def __init__(self, chat_id, debounce_function, function_args=None, delay=15, ):
        if function_args is None:
            function_args = []
        self.chat_id = chat_id
        self.delay = delay
        self.current_timer = threading.Timer(self.delay, self._flush_buffer)
        self.debounce_function = debounce_function
        self.function_args = function_args

    @property
    def buffer_key(self):
        return f"chat_buffer:{self.chat_id}"

    @property
    def lock_key(self):
        return f"chat_lock:{self.chat_id}"

    def add_message(self, message_text):
        messages = cache.get_or_set(self.buffer_key, [])
        messages.append(message_text)
        cache.set(self.buffer_key, messages)

        added = cache.add(self.lock_key, "processing", timeout=self.delay)
        if not added:
            self.current_timer.cancel()
        self.current_timer.start()
        return added

    def _flush_buffer(self):
        """Recupera todos los mensajes, los concatena y los procesa."""
        messages = cache.get(self.buffer_key, [])
        if not messages:
            return

        full_messages = "\n".join(messages)
        self.debounce_function(*self.function_args, full_messages)
        cache.delete(self.lock_key)
