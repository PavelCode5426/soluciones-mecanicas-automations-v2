from django.urls import path

from whatsapp import views

app_name = 'whatsapp'

urlpatterns = [
    path(r'chats-webhook', views.WhatsAppChatsWebhookView.as_view(), name='chats-webhook'),
    path(r'groups-webhook', views.WhatsAppGroupEventWebhook.as_view(), name='groups-webhook'),
]
