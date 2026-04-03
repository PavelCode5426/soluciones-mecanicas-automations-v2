from django.urls import path, include
from whatsapp import views

app_name = 'whatsapp'

urlpatterns = [
    path(r'webhook/<str:session>', views.WhatsAppMessageWebhookView.as_view(), name='message-webhook'),
    path(r'leads-explorer', views.WhatsAppLeadWebhookView.as_view(), name='lead-webhook'),
]
