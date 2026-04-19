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
    path(r'status/<int:pk>/toggle-status', views.WhatsAppStatusToggleStatusView.as_view(),
         name='status.toggle-status'),

    path(r'contacts', views.WhatsAppContactsListView.as_view(), name='contacts.index'),
    path(r'contacts/<int:pk>/edit', views.WhatsAppContactsUpdateView.as_view(), name='contacts.update'),
    path(r'contacts/<int:pk>/delete', views.WhatsAppContactsDeleteView.as_view(), name='contacts.delete'),
    path(r'contacts/<int:pk>/toggle-status', views.WhatsAppContactsToggleStatusView.as_view(),
         name='contacts.toggle-status'),

    path(r'groups', views.WhatsAppGroupsListView.as_view(), name='groups.index'),
    path(r'groups/<int:pk>/toggle-status', views.WhatsAppGroupsToggleStatusView.as_view(),
         name='groups.toggle-status'),

    path(r'accounts', views.WhatsAppAccountsListView.as_view(), name='accounts.index'),
    path(r'accounts/create', views.WhatsAppAccountsCreateView.as_view(), name='accounts.create'),
    path(r'accounts/<int:pk>/edit', views.WhatsAppAccountsUpdateView.as_view(), name='accounts.update'),
    path(r'accounts/<int:pk>/delete', views.WhatsAppAccountsDeleteView.as_view(), name='accounts.delete'),
    path(r'accounts/<int:pk>/toggle-status', views.WhatsAppAccountsToggleStatusView.as_view(),
         name='accounts.toggle-status'),

]
