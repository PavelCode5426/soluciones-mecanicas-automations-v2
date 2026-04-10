import asyncio
import base64
import time

from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet
from django_q.tasks import async_task
from llama_index.core.memory import Memory
from workflows import Context

from ia_assistant.factories import retrieve_agent_from_application, retrieve_memory_blocks_from_application
from services.agents import WhatsAppLeadAnalyzer
from services.whatsapp import WAHAService
from whatsapp.factories import create_whatsapp_service
from whatsapp.helpers import get_file_mimetype
from whatsapp.models import WhatsAppAccount, WhatsAppGroup, WhatsAppContact, WhatsAppStatus, WhatsAppMessage, \
    WhatsAppAutoReplyMessage, WhatsAppLead, WhatsAppProcessedLead


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
        caption = status.message
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


def send_message(message: WhatsAppMessage | WhatsAppAutoReplyMessage, chat_id: str, typing_timeout=None):
    message.refresh_from_db()
    if message.active and message.account.active:
        service = create_whatsapp_service(message.account)
        caption = message.message
        mimetype = message.message_type
        file = {
            "mimetype": get_file_mimetype(message.file),
            "data": base64.b64encode(message.file.read()).decode('utf-8'),
        } if message.file else None
        message_presence = "recording" if 'audio' in mimetype else "typing"

        typing_timer = max(10, int(len(caption) * 0.3)) if typing_timeout is None else typing_timeout

        while typing_timer > 0:
            service.set_chat_presence(chat_id, message_presence)
            typing_timer -= 5
            time.sleep(5)

        if message.message_type == 'list':
            service.send_list_message({
                "chatId": chat_id,
                "reply_to": None,
                "message": {
                    "title": message.title,
                    "description": message.description,
                    "footer": message.footer,
                    "button": message.button_label,
                    "sections": message.sections
                }})
        elif file:
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


def enqueue_simple_message(message: WhatsAppMessage | WhatsAppAutoReplyMessage, chat_id: str, typing_timeout=None):
    cluster = 'whatsapp'
    group = 'whatsapp_message'
    task_name = f"send_{message.message_type}_{message.pk}_to_{chat_id}".lower()
    async_task(send_message, message, chat_id, typing_timeout, task_name=task_name, group=group, cluster=cluster)


def enqueue_whatsapp_message(message: WhatsAppMessage, refresh: bool = True):
    if refresh:
        message.refresh_from_db()
    if message.active:
        contacts_and_groups = []
        for distribution_list in message.distribution_lists.prefetch_related('groups', 'contacts').all():
            contacts = distribution_list.contacts.filter(active=True).all()
            groups = distribution_list.groups.filter(active=True).all()
            contacts_and_groups.extend([g.chat_id for g in groups])
            contacts_and_groups.extend([c.chat_id for c in contacts])

        for chat_id in contacts_and_groups:
            enqueue_simple_message(message, chat_id)


def enqueue_whatsapp_auto_reply_message(message: WhatsAppAutoReplyMessage, chat_id: str):
    message.refresh_from_db()
    enqueue_simple_message(message, chat_id, 10)


def send_message_to_lead(lead: WhatsAppLead):
    lead.refresh_from_db()
    all_messages = WhatsAppLead.objects.select_related('group') \
        .filter(chat_id=lead.chat_id, processed=False, account=lead.account).all()

    messages = []
    groups = []

    for m in all_messages:
        if m.message not in messages:
            messages.append(m.message)
        if m.group.name not in groups:
            groups.append(m.group.name)

    long_messages = "\n".join(messages)
    all_groups = ", ".join(groups)

    async def main():
        analyzer = WhatsAppLeadAnalyzer(lead.account.lead_prompt)
        return await analyzer.run(messages=long_messages, groups=all_groups, profile=lead.chat_name)

    response = asyncio.run(main())

    if response.is_relevant:
        create_whatsapp_service(lead.account).send_text_message({
            "chatId": lead.chat_id,
            "reply_to": None,
            "text": response.promotional_message,
            "linkPreview": False,
            "linkPreviewHighQuality": False
        })
    all_messages.delete()
    WhatsAppProcessedLead.objects.create(chat_id=lead.chat_id, account=lead.account, chat_name=lead.chat_name,
                                         group=lead.group, message=long_messages,
                                         message_reply=response.promotional_message, processed=True)
    return response.promotional_message


def enqueue_create_message_for_lead(leads: QuerySet[WhatsAppLead]):
    for lead in leads:
        async_task(send_message_to_lead, lead, cluster='whatsapp')


def ___keep_typing_loop_task(service: WAHAService, chat_id):
    async def __keep_typing():
        try:
            while True:
                service.start_typing(chat_id)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            service.stop_typing(chat_id)

    return asyncio.create_task(__keep_typing())


def enqueue_reply_using_ia(account: WhatsAppAccount, chat_id: str, message: str):
    account.refresh_from_db()
    if account.active and account.can_reply_with_ia and account.ia_application:
        ia_application = account.ia_application
        agent = retrieve_agent_from_application(ia_application)
        memory = Memory.from_defaults(
            chat_id,
            memory_blocks=retrieve_memory_blocks_from_application(ia_application)
        )
        whatsapp_service = create_whatsapp_service(account)

        async def main():
            previus_context = cache.get_or_set(chat_id, {})
            ctx = Context(agent, previous_context=previus_context)
            typing_task = ___keep_typing_loop_task(whatsapp_service, chat_id)
            try:
                async with asyncio.timeout(settings.LLAMAINDEX_TIMEOUT):
                    response = await agent.run(message, ctx=ctx, memory=memory)
                    response = str(response).replace("**", "*")
                    whatsapp_service.send_simple_text_message(chat_id, response)
            finally:
                typing_task.cancel()
            cache.set(chat_id, ctx.to_dict())

        if '--reset' in message:
            cache.delete(chat_id)
            whatsapp_service.send_simple_text_message(chat_id, "👌")
        else:
            asyncio.run(main(), debug=True)
