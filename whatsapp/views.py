from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from whatsapp.models import WhatsAppAccount, WhatsAppLead, WhatsAppGroup, WhatsAppAutoReplyMessage
from whatsapp.tasks import enqueue_whatsapp_auto_reply_message


class WhatsAppEventsWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        account = WhatsAppAccount.objects.get(active=True, session=request.data.get('session'))
        payload = request.data.get('payload')
        info = payload.get('_data').get('Info')

        has_media = payload.get('hasMedia')
        is_from_me = payload.get('fromMe')
        is_group = info.get('IsGroup')

        sender = info.get('Sender')
        sender_name = info.get('PushName')
        message = payload.get('body')
        media_url = None if not has_media else payload.get('media').get('url').replace("http://localhost:3000",
                                                                                       settings.WAHA_SERVER_URL)

        if is_group and account.can_find_leads and message and not is_from_me:
            group = WhatsAppGroup.objects.filter(chat_id=info.get('Chat')).first()
            WhatsAppLead.objects.create(account=account, group=group, message=message,
                                        chat_id=sender, media_url=media_url, chat_name=sender_name)

        elif account.can_auto_reply:
            automatic_message = self.__send_auto_message(account, message, sender)
            if automatic_message is None and account.can_use_ia:
                self.__reply_using_ia(account, message, sender)

        return Response(status=status.HTTP_200_OK)

    def __send_auto_message(self, account, message, chat_id):
        auto_message = WhatsAppAutoReplyMessage.objects \
            .filter(account=account, trigger_message=message, active=True).first()
        if auto_message:
            enqueue_whatsapp_auto_reply_message(message=auto_message, chat_id=chat_id)

        return auto_message

    def __reply_using_ia(self, account, message, chat_id):
        pass
