import base64

from crum import get_current_request

from whatsapp.factories import create_whatsapp_service
from whatsapp.helpers import get_file_mimetype
from whatsapp.models import WhatsAppAccount, WhatsAppGroup, WhatsAppContact, WhatsAppStatus


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
