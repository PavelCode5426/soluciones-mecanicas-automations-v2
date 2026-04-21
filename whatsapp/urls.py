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
    path(r'accounts/<int:pk>/details', views.WhatsAppAccountDetailView.as_view(), name='accounts.details'),
    path(r'accounts/<int:pk>/update-groups', views.WhatsAppAccountSynchronizeGroupsView.as_view(),
         name='accounts.update-groups'),

    path(r'accounts/<int:pk>/sort-messages', views.WhatsAppMessagesSorterView.as_view(), name='accounts.sort-messages'),

    path(r'accounts/<int:pk>/update-contacts', views.WhatsAppAccountSynchronizeContactsView.as_view(),
         name='accounts.update-contacts'),

    path(r'distribution-lists', views.WhatsAppDistributionListsListView.as_view(), name='distribution-lists.index'),
    path(r'distribution-lists/create', views.WhatsAppDistributionListsCreateView.as_view(),
         name='distribution-lists.create'),
    path(r'distribution-lists/<int:pk>/edit', views.WhatsAppDistributionListsUpdateView.as_view(),
         name='distribution-lists.update'),
    path(r'distribution-lists/<int:pk>/delete', views.WhatsAppDistributionListsDeleteView.as_view(),
         name='distribution-lists.delete'),
    path(r'distribution-lists/<int:pk>/toggle-status', views.WhatsAppDistributionListsToggleStatusView.as_view(),
         name='distribution-lists.toggle-status'),

    path(r'messages', views.WhatsAppMessagesListView.as_view(), name='messages.index'),
    path(r'messages/create', views.WhatsAppMessageCreateView.as_view(), name='messages.create'),
    path(r'messages/<int:pk>/edit', views.WhatsAppMessageUpdateView.as_view(), name='messages.update'),
    path(r'messages/<int:pk>/delete', views.WhatsAppMessageDeleteView.as_view(),
         name='messages.delete'),
    path(r'messages/<int:pk>/toggle-status', views.WhatsAppMessageToggleStatusView.as_view(),
         name='messages.toggle-status'),

]
