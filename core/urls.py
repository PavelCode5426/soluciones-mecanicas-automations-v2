from django.urls import path

from . import views

urlpatterns = [
    path(r'login', views.LoginView.as_view(), name='authentication.login'),
    path(r'reset-password', views.PasswordResetView.as_view(), name='authentication.reset_password.index'),
    path("reset-password/done", views.PasswordResetDoneView.as_view(), name="authentication.reset_password.done"),
    path("reset-password/<uidb64>/<token>", views.PasswordResetConfirmView.as_view(),
         name="authentication.reset_password.confirm"),
    path("reset-password/complete", views.PasswordResetCompleteView.as_view(),
         name="authentication.reset_password.complete"),
    path(r'logout', views.LogoutView.as_view(), name='authentication.logout'),

    path(r'', views.IndexView.as_view(), name='index'),

]
