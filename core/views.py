from django.contrib.auth import views as auth_view
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView


# Create your views here.

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'core/index.html'


class LoginView(auth_view.LoginView):
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True


class LogoutView(auth_view.LogoutView):
    pass


class PasswordResetView(auth_view.PasswordResetView):
    template_name = 'authentication/reset_password/index.html'


class PasswordResetDoneView(auth_view.PasswordResetDoneView):
    template_name = 'authentication/reset_password/done.html'


class PasswordResetConfirmView(auth_view.PasswordResetConfirmView):
    success_url = reverse_lazy('authentication.reset_password.complete')
    template_name = 'authentication/reset_password/confirm.html'


class PasswordResetCompleteView(auth_view.PasswordResetCompleteView):
    template_name = 'authentication/reset_password/complete.html'
