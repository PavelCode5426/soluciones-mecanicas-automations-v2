from django.urls import path, include
from whatsapp import views

app_name = 'whatsapp'

urlpatterns = [
    path(r'whatsapp-message/<str:application_name>', views.WhatsAppMessageWebhookView.as_view(), name='webhook'),
]
