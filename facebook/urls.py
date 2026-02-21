from django.urls import path, include
from facebook import views

urlpatterns = [
    path('whatsapp-message', views.WhatsAppMessageWebhookView.as_view(), name='whatsapp-webhook'),
]
