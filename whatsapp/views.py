from django.conf import settings
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from whatsapp.models import WhatsAppAccount, WhatsAppLead, WhatsAppGroup, WhatsAppAutoReplay
from whatsapp.tasks import send_whatsapp_autoreplay_message


# Create your views here.
class WhatsAppMessageWebhookView(GenericAPIView):
    lookup_field = 'session'
    lookup_url_kwarg = 'session'
    queryset = WhatsAppAccount.objects.filter(active=True)

    def post(self, request, *args, **kwargs):
        payload = request.data.get('payload')
        is_from_me = payload.get('fromMe')
        from_id = payload.get('from')
        message_type = payload.get('_data').get('Info').get('Type')
        account = self.get_object() if not is_from_me else self.get_object()

        if account.can_use_webhook:
            if message_type == 'text':
                message = payload.get('body')
                # async_task(reply_whatsapp_message, rag.name, message, from_id, group='ia_assistant',
                #            task_name=f"whatsapp_message_{from_id}".lower(), cluster='high_priority')

        return Response(status=status.HTTP_200_OK)


class WhatsAppLeadWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        account = WhatsAppAccount.objects.get(active=True, session=request.data.get('session'))
        payload = request.data.get('payload')
        info = payload.get('_data').get('Info')

        has_media = payload.get('hasMedia')
        is_from_me = payload.get('fromMe')
        is_group = info.get('IsGroup')

        group = WhatsAppGroup.objects.get(chat_id=info.get('Chat'))
        sender = info.get('Sender')
        sender_name = info.get('PushName')
        message = payload.get('body')
        media_url = None if not has_media else payload.get('media').get('url').replace("http://localhost:3000",
                                                                                       settings.WAHA_SERVER_URL)

        if is_group and message and not is_from_me:
            WhatsAppLead.objects.create(
                account=account, group=group, message=message,
                chat_id=sender, media_url=media_url, chat_name=sender_name,
            )
        elif not is_from_me:
            auto_message = (WhatsAppAutoReplay.objects
                            .filter(account=account, trigger_message__icontains=message).first())
            if auto_message:
                send_whatsapp_autoreplay_message(auto_message, chat_id=sender)
        return Response(status=status.HTTP_200_OK)
