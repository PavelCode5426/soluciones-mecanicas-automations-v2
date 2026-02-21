from django_q.tasks import async_task
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from facebook.tasks import reply_whatsapp_message


class WhatsAppMessageWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        payload = request.data.get('payload')

        from_id = payload.get('from')
        account_name = payload.get('PushName')
        message_type = payload.get('_data').get('Info').get('Type')
        if message_type == 'text':
            message = payload.get('body')
            async_task(reply_whatsapp_message, message, from_id, account_name,
                       task_name=f"whatsapp_message_{account_name}".lower(), cluster='high_priority')

        return Response(status=status.HTTP_200_OK)
