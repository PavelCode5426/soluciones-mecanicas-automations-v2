from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from whatsapp.factories import create_whatsapp_service
from whatsapp.helpers import ChatMessageDebouncer, get_or_set_chat_debouncer
from whatsapp.models import WhatsAppAccount, WhatsAppLead, WhatsAppGroup, WhatsAppAutoReplyMessage, \
    WhatsAppProcessedLead
from whatsapp.tasks import enqueue_whatsapp_auto_reply_message, enqueue_reply_using_ia


class WhatsAppWebhookMixins:
    def transform_payload(self, request):
        payload = request.data.get('payload')
        info = payload.get('_data').get('Info')

        has_media = payload.get('hasMedia')
        is_from_me = payload.get('fromMe')
        is_group = info.get('IsGroup')

        sender = info.get('Sender')
        sender_name = info.get('PushName')
        message = payload.get('body')
        media_url = None if not has_media else payload.get('media').get('url', '').replace("http://localhost:3000",
                                                                                           settings.WAHA_SERVER_URL)

        return {
            'payload': payload,
            'info': info,
            'has_media': has_media,
            'is_from_me': is_from_me,
            'is_group': is_group,
            'sender': sender,
            'sender_name': sender_name,
            'message': message,
            'media_url': media_url,
            'chat_id': info.get('Chat')
        }

    def get_account(self, request):
        session = request.data.get('session')
        return cache.get_or_set(session, WhatsAppAccount.objects.get(active=True, session=session))


class WhatsAppChatsWebhookView(APIView, WhatsAppWebhookMixins):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        account = self.get_account(request)
        payload = self.transform_payload(request)
        is_group = payload.get('is_group')
        message = payload.get('message')
        is_from_me = payload.get('is_from_me')
        sender = payload.get('sender')

        if not is_group and not is_from_me and account.can_auto_reply:
            # last_message_timestamp = create_whatsapp_service(account).get_last_message_timestamp(sender)
            # if (int(now().timestamp()) - last_message_timestamp) >= 24 * 3600 and account.automatic_message:
            #     enqueue_whatsapp_auto_reply_message(message=account.automatic_message, chat_id=sender)
            # else:
            automatic_message = self.__send_auto_message(account, message, sender)
            if automatic_message is None and account.can_reply_with_ia:
                self.__reply_using_ia(account, message, sender)

        return Response(status=status.HTTP_200_OK)

    def __send_auto_message(self, account, message, chat_id):
        auto_message = WhatsAppAutoReplyMessage.objects \
            .filter(account=account, trigger_message=message, active=True).first()
        if auto_message:
            enqueue_whatsapp_auto_reply_message(message=auto_message, chat_id=chat_id)

        return auto_message

    def __reply_using_ia(self, account, message, chat_id):
        debouncer = get_or_set_chat_debouncer(
            chat_id,
            ChatMessageDebouncer(
                chat_id,
                debounce_function=enqueue_reply_using_ia,
                function_args=[account, chat_id])
        )
        debouncer.add_message(message)


class WhatsAppGroupEventWebhook(APIView, WhatsAppWebhookMixins):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        account = self.get_account(request)
        payload = self.transform_payload(request)
        is_group = payload.get('is_group')
        message = payload.get('message')
        is_from_me = payload.get('is_from_me')
        sender_name = payload.get('sender_name', "")
        sender = payload.get('sender')
        chat_id = payload.get('chat_id')
        media_url = payload.get('media_url')

        if is_group and account.can_find_leads and message and not is_from_me and 'promo' not in sender_name.lower():
            group = WhatsAppGroup.objects.filter(chat_id=chat_id).first()
            if group and not WhatsAppProcessedLead.objects.filter(chat_id=chat_id).exists():
                WhatsAppLead.objects.create(account=account, group=group, message=message,
                                            chat_id=sender, media_url=media_url, chat_name=sender_name)
        return Response(status=status.HTTP_200_OK)
