import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class WhatsAppMessageWebhookView(APIView):

    def get(self, request, *args, **kwargs):
        get_params = dict(request.GET)
        body_raw = request.body.decode('utf-8', errors='ignore')
        try:
            json_data = json.loads(body_raw) if body_raw else {}
        except:
            json_data = "No es JSON válido"

        print(get_params)
        print(json_data)
        return Response(status=status.HTTP_200_OK)
