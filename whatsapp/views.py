from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django_filters.views import FilterView

from core.generics import ToggleStatusView
from whatsapp import filters
from whatsapp import models, forms
from whatsapp.mixins import WhatsAppAccountViewMixins


class WhatsAppStatusListView(FilterView):
    template_name = 'whatsapp/status/index.html'
    filterset_class = filters.WhatsAppStatusFilterSet
    queryset = models.WhatsAppStatus.objects.all()
    paginate_by = 100


class WhatsAppStatusCreateView(CreateView):
    success_url = reverse_lazy('whatsapp:status.index')
    form_class = forms.WhatsAppStatusForm
    template_name = 'whatsapp/status/create_or_update.html'
    extra_context = {
        "page_title": "Crear nuevo estado",
        "cancel_url": success_url
    }


class WhatsAppStatusUpdateView(UpdateView):
    success_url = reverse_lazy('whatsapp:status.index')
    form_class = forms.WhatsAppStatusForm
    queryset = models.WhatsAppStatus.objects.all()
    template_name = 'whatsapp/status/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar {{instance}}",
        "cancel_url": success_url
    }


class WhatsAppStatusToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:status.index')
    queryset = models.WhatsAppStatus.objects.all()
    success_message = "Estado {instance} activado/desactivado exitosamente"


class WhatsAppContactsListView(FilterView):
    template_name = 'whatsapp/contacts/index.html'
    filterset_class = filters.WhatsAppGenericFilterSet
    queryset = models.WhatsAppContact.objects.all()
    paginate_by = 100


class WhatsAppContactsUpdateView(UpdateView):
    success_url = reverse_lazy('whatsapp:contacts.index')
    template_name = 'whatsapp/contacts/create_or_update.html'
    form_class = forms.WhatsAppContactForm
    queryset = models.WhatsAppContact.objects.all()
    extra_context = {
        "page_title": "Actualizar contacto",
        "cancel_url": success_url
    }


class WhatsAppContactsDeleteView(SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy('whatsapp:contacts.index')
    queryset = models.WhatsAppContact.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar contacto",
        "modal_title": "Eliminar contacto",
        "modal_description": "Eliminar contacto",
        "cancel_url": success_url
    }
    success_message = "Contacto {instance} eliminada exitosamente"


class WhatsAppContactsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:contacts.index')
    queryset = models.WhatsAppContact.objects.all()
    success_message = "Contacto {instance} activado/desactivado exitosamente"


class WhatsAppGroupsListView(FilterView):
    template_name = 'whatsapp/groups/index.html'
    filterset_class = filters.WhatsAppGenericFilterSet
    queryset = models.WhatsAppGroup.objects.all()
    paginate_by = 100


class WhatsAppGroupsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:groups.index')
    queryset = models.WhatsAppGroup.objects.all()
    success_message = "Grupo {instance} activado/desactivado exitosamente"


class WhatsAppAccountsListView(ListView):
    template_name = 'whatsapp/accounts/index.html'
    queryset = models.WhatsAppAccount.objects.all()


class WhatsAppAccountsCreateView(WhatsAppAccountViewMixins, SuccessMessageMixin, CreateView):
    success_url = reverse_lazy('whatsapp:accounts.index')
    form_class = forms.WhatsAppCreateAccountForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nueva cuenta",
        "cancel_url": success_url
    }
    success_message = "Cuenta creada exitosamente"


class WhatsAppAccountsUpdateView(WhatsAppAccountViewMixins, SuccessMessageMixin, UpdateView):
    success_url = reverse_lazy('whatsapp:accounts.index')
    form_class = forms.WhatsAppUpdateAccountForm
    queryset = models.WhatsAppAccount.objects.all()
    template_name = 'whatsapp/accounts/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar cuenta",
        "cancel_url": success_url
    }
    success_message = "Cuenta {instance} actualizada exitosamente"


class WhatsAppAccountsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:accounts.index')
    queryset = models.WhatsAppAccount.objects.all()
    success_message = "Cuenta {instance} activada/desactivada exitosamente"


class WhatsAppAccountsDeleteView(SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy('whatsapp:accounts.index')
    queryset = models.WhatsAppAccount.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar cuenta",
        "modal_title": "Eliminar cuenta",
        "modal_description": "Eliminar cuenta",
        "cancel_url": success_url
    }
    success_message = "Cuenta {instance} eliminada exitosamente"
