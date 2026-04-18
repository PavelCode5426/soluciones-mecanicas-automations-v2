from django.urls import path

from whatsapp import views
from whatsapp import webhooks

app_name = 'whatsapp'

urlpatterns = [
    path(r'chats-webhook', webhooks.WhatsAppChatsWebhookView.as_view(), name='chats-webhook'),
    path(r'groups-webhook', webhooks.WhatsAppGroupEventWebhook.as_view(), name='groups-webhook'),

    path(r'status', views.WhatsAppStatusListView.as_view(), name='status.index'),
    path(r'status/create', views.WhatsAppStatusCreateView.as_view(), name='status.create'),
    path(r'status/<int:pk>/edit', views.WhatsAppStatusUpdateView.as_view(), name='status.update'),

    path(r'contacts', views.WhatsAppContactsListView.as_view(), name='contacts.index'),
    path(r'groups', views.WhatsAppGroupsListView.as_view(), name='groups.index'),

]
