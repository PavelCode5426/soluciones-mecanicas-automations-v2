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
]
