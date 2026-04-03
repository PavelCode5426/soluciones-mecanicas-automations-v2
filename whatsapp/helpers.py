import asyncio
import mimetypes
import os

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


def keep_typing_loop_task(service: WAHAService, chat_id):
    async def __keep_typing():
        try:
            while True:
                service.start_typing(chat_id)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            service.stop_typing(chat_id)

    return asyncio.create_task(__keep_typing())
