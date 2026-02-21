from django.urls import path, include
from facebook import views

app_name = 'facebook'

urlpatterns = [
    path(r'whatsapp-message', views.WhatsAppMessageWebhookView.as_view(), name='whatsapp-webhook'),
]
