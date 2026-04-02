from django_q.tasks import async_task
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from ia_assistant.models import RAGApplication
from ia_assistant.tasks import reply_whatsapp_message


