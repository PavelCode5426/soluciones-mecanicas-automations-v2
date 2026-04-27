from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from core.generics import ToggleStatusView
from facebook import forms
from facebook import models


class FacebookAccountsListView(ListView):
    template_name = 'facebook/accounts/index.html'
    queryset = models.FacebookProfile.objects.all()


class FacebookAccountDetailView(DetailView):
    queryset = models.FacebookProfile.objects.all()
    template_name = 'whatsapp/accounts/details.html'



class FacebookAccountsCreateView(SuccessMessageMixin, CreateView):
    success_url = reverse_lazy('facebook:accounts.index')
    form_class = forms.FacebookUpdateAccountForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nueva cuenta",
        "cancel_url": success_url
    }
    success_message = "Cuenta creada exitosamente"


class FacebookAccountsUpdateView(SuccessMessageMixin, UpdateView):
    success_url = reverse_lazy('facebook:accounts.index')
    form_class = forms.FacebookUpdateAccountForm
    queryset = models.FacebookProfile.objects.all()
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Actualizar cuenta: ",
        "cancel_url": success_url
    }
    success_message = "Cuenta object actualizada exitosamente"


class FacebookAccountsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:accounts.index')
    queryset = models.FacebookProfile.objects.all()
    success_message = "Cuenta object activada/desactivada exitosamente"

class FacebookAccountsDeleteView(SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy('whatsapp:accounts.index')
    queryset = models.FacebookProfile.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar cuenta: ",
        "modal_title": "Eliminar cuenta: ",
        "modal_description": "Eliminar cuenta: ",
        "cancel_url": success_url
    }
    success_message = "Cuenta object eliminada exitosamente"
