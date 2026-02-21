import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class WhatsAppMessageWebhookView(APIView):

    def dispatch(self, request, *args, **kwargs):
        print(request.GET)
        print(request.POST)
        print(request.body)
        print(request.data)
        return Response(status=status.HTTP_200_OK)
