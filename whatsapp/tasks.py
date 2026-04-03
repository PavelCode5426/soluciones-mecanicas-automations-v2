import base64
import time
from whatsapp.factories import create_whatsapp_service
from whatsapp.helpers import get_file_mimetype, keep_presence_loop_task
from whatsapp.models import WhatsAppAccount, WhatsAppGroup, WhatsAppContact, WhatsAppStatus, WhatsAppMessage


def syncronize_whatsapp_account_groups(account: WhatsAppAccount):
    service = create_whatsapp_service(account)
    account_groups = service.get_all_groups()
    for group in account_groups:
        chat_id = group['JID']
        name = group['Name']
        is_locked = group['IsLocked']
        is_ephemeral = group['IsEphemeral']
        participant_count = group['ParticipantCount']

        if name:
            WhatsAppGroup.objects.update_or_create(
                defaults=dict(
                    name=name,
                    is_locked=is_locked,
                    is_ephemeral=is_ephemeral,
                    participant_count=participant_count
                ),
                create_defaults=dict(
                    name=name,
                    is_locked=is_locked,
                    is_ephemeral=is_ephemeral,
                    participant_count=participant_count,
                    account=account
                ),
                chat_id=chat_id, account=account
            )


def syncronize_whatsapp_account_contacts(account: WhatsAppAccount):
    service = create_whatsapp_service(account)
    contacts = service.get_all_contacts()
    for contact in contacts:
        chat_id = contact['id']
        name = contact['name']
        push_name = contact['pushname']

        if name:
            WhatsAppContact.objects.update_or_create(
                defaults=dict(name=name, push_name=push_name),
                create_defaults=dict(name=name, push_name=push_name, account=account),
                chat_id=chat_id, account=account
            )


def publish_whatsapp_status(status: WhatsAppStatus):
    status.refresh_from_db()
    if status.active:
        service = create_whatsapp_service(status.account)
        caption = status.caption
        backgroundColor = '#38b42f'
        font = 0

        if status.file:
            mimetype = status.message_type
            file_status = {
                "file": {
                    "mimetype": get_file_mimetype(status.file),
                    "data": base64.b64encode(status.file.read()).decode('utf-8'),
                },
                "caption": caption,
                "backgroundColor": backgroundColor
            }

            if 'video' in mimetype:
                service.create_whatsapp_video(file_status)
            elif 'audio' in mimetype:
                service.create_voice_status(file_status)
            elif 'image' in mimetype:
                service.create_image_status(file_status)
        else:
            service.create_text_status({
                "id": None,
                "contacts": None,
                "text": caption,
                "font": font,
                "backgroundColor": backgroundColor,
                "linkPreview": False,
                "linkPreviewHighQuality": False
            })


def send_whatsapp_message(message: WhatsAppMessage):
    message.refresh_from_db()
    if message.active:
        service = create_whatsapp_service(message.account)
        caption = message.message
        typing_timer = max(10, int(len(caption) * 0.5))
        mimetype = message.message_type
        file = {
            "mimetype": get_file_mimetype(message.file),
            "data": base64.b64encode(message.file.read()).decode('utf-8'),
        } if message.file else None
        message_presence = "recording" if 'audio' in mimetype else "typing"

        contacts_and_groups = []
        for distribution_list in message.distribution_lists.prefetch_related('groups', 'contacts').all():
            contacts = distribution_list.contacts.filter(active=True).all()
            groups = distribution_list.groups.filter(active=True, is_locked=False).all()
            contacts_and_groups.extend([g.chat_id for g in groups])
            contacts_and_groups.extend([c.chat_id for c in contacts])

        while len(contacts_and_groups) > 0:
            chat_id = contacts_and_groups.pop(0)
            service.set_chat_presence(chat_id, message_presence)
            time.sleep(typing_timer)
            if file:
                file_message = {"chatId": chat_id, "reply_to": None, "file": file, "caption": caption}
                if 'video' in mimetype:
                    service.send_video_message(file_message)
                elif 'audio' in mimetype:
                    service.send_voice_message(file_message)
                elif 'image' in mimetype:
                    service.send_image_message(file_message)
                elif 'file' in mimetype:
                    service.send_file_message(file_message)
            else:
                service.send_text_message({
                    "chatId": chat_id,
                    "reply_to": None,
                    "text": caption,
                    "linkPreview": False,
                    "linkPreviewHighQuality": False
                })
            service.set_chat_presence(chat_id, 'paused')
