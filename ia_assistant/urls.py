from django.urls import path, include
from ia_assistant import views

app_name = 'ia_assistant'

urlpatterns = [
    path(r'whatsapp-message/<str:application_name>', views.WhatsAppMessageWebhookView.as_view(), name='whatsapp-webhook'),
]
