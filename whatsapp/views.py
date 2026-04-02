from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from whatsapp.models import WhatsAppAccount


# Create your views here.
class WhatsAppMessageWebhookView(GenericAPIView):
    lookup_field = 'name'
    lookup_url_kwarg = 'application_name'
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
