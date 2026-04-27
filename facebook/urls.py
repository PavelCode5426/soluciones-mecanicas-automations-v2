from django.urls import path

from facebook import views

app_name = 'facebook'

urlpatterns = [
    path(r'accounts', views.FacebookAccountsListView.as_view(), name='accounts.index'),
    path(r'accounts/create', views.FacebookAccountsCreateView.as_view(), name='accounts.create'),
    path(r'accounts/<int:pk>/edit', views.FacebookAccountsUpdateView.as_view(), name='accounts.update'),
    path(r'accounts/<int:pk>/delete', views.FacebookAccountsDeleteView.as_view(), name='accounts.delete'),
    path(r'accounts/<int:pk>', views.FacebookAccountDetailView.as_view(), name='accounts.details'),
    path(r'accounts/<int:pk>/toggle-status', views.FacebookAccountsToggleStatusView.as_view(),
         name='accounts.toggle-status'),

    path(r'groups', views.FacebookGroupsListView.as_view(), name='groups.index'),
    path(r'groups/<int:pk>/toggle-status', views.FacebookGroupsToggleStatusView.as_view(),
         name='groups.toggle-status'),

    path(r'agents', views.FacebookAgentListView.as_view(), name='agents.index'),
    path(r'agents/create', views.FacebookAgentCreateView.as_view(), name='agents.create'),
    path(r'agents/<int:pk>/edit', views.FacebookAgentUpdateView.as_view(), name='agents.update'),
    path(r'agents/<int:pk>/delete', views.FacebookAgentToggleStatusView.as_view(), name='agents.delete'),
    path(r'agents/<int:pk>', views.FacebookAgentDetailView.as_view(), name='agents.details'),
    path(r'agents/<int:pk>/toggle-status', views.FacebookAgentToggleStatusView.as_view(), name='agents.toggle-status'),

    path(r'distribution-lists', views.FacebookDistributionListsListView.as_view(), name='distribution-lists.index'),
    path(r'distribution-lists/create', views.FacebookDistributionListsCreateView.as_view(),
         name='distribution-lists.create'),
    path(r'distribution-lists/<int:pk>/edit', views.FacebookDistributionListsUpdateView.as_view(),
         name='distribution-lists.update'),
    path(r'distribution-lists/<int:pk>/delete', views.FacebookDistributionListsDeleteView.as_view(),
         name='distribution-lists.delete'),
    path(r'distribution-lists/<int:pk>/toggle-status', views.FacebookDistributionListsToggleStatusView.as_view(),
         name='distribution-lists.toggle-status'),

]
