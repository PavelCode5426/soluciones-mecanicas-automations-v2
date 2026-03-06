from django_q.tasks import async_task
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ia_assistant.tasks import reply_whatsapp_message


class WhatsAppMessageWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        payload = request.data.get('payload')
        print(payload)
        is_from_me = payload.get('fromMe')
        if not is_from_me:
            from_id = payload.get('from')
            message_type = payload.get('_data').get('Info').get('Type')
            if message_type == 'text':
                message = payload.get('body')
                async_task(reply_whatsapp_message, message, from_id,
                           group_name='ia_assistant',
                           task_name=f"whatsapp_message_{from_id}".lower(),
                           cluster='high_priority')

        return Response(status=status.HTTP_200_OK)
