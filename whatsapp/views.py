from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django_filters.views import FilterView

from core.generics import ToggleStatusView, SingleFormView
from whatsapp import filters
from whatsapp import models, forms
from whatsapp.mixins import WhatsAppAccountViewMixins
from whatsapp.tasks import syncronize_whatsapp_account_groups, syncronize_whatsapp_account_contacts


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
        "page_title": "Actualizar estado: ",
        "cancel_url": success_url
    }


class WhatsAppStatusToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:status.index')
    queryset = models.WhatsAppStatus.objects.all()
    success_message = "Estado object activado/desactivado exitosamente"


class WhatsAppContactsListView(FilterView):
    template_name = 'whatsapp/contacts/index.html'
    filterset_class = filters.WhatsAppContactsFilterSet
    queryset = models.WhatsAppContact.objects.all()
    paginate_by = 100


class WhatsAppContactsUpdateView(UpdateView):
    success_url = reverse_lazy('whatsapp:contacts.index')
    template_name = 'whatsapp/contacts/create_or_update.html'
    form_class = forms.WhatsAppContactForm
    queryset = models.WhatsAppContact.objects.all()
    extra_context = {
        "page_title": "Actualizar contacto: ",
        "cancel_url": success_url
    }


class WhatsAppContactsDeleteView(SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy('whatsapp:contacts.index')
    queryset = models.WhatsAppContact.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar contacto: ",
        "modal_title": "Eliminar contacto: ",
        "modal_description": "Eliminar contacto",
        "cancel_url": success_url
    }
    success_message = "Contacto {object} eliminada exitosamente"


class WhatsAppContactsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:contacts.index')
    queryset = models.WhatsAppContact.objects.all()
    success_message = "Contacto object activado/desactivado exitosamente"


class WhatsAppGroupsListView(FilterView):
    template_name = 'whatsapp/groups/index.html'
    filterset_class = filters.WhatsAppGroupsFilterSet
    queryset = models.WhatsAppGroup.objects.all()
    paginate_by = 100


class WhatsAppGroupsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:groups.index')
    queryset = models.WhatsAppGroup.objects.all()
    success_message = "Grupo object activado/desactivado exitosamente"


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
        "page_title": "Actualizar cuenta: ",
        "cancel_url": success_url
    }
    success_message = "Cuenta object actualizada exitosamente"


class WhatsAppAccountsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:accounts.index')
    queryset = models.WhatsAppAccount.objects.all()
    success_message = "Cuenta object activada/desactivada exitosamente"


class WhatsAppAccountsDeleteView(SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy('whatsapp:accounts.index')
    queryset = models.WhatsAppAccount.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar cuenta: ",
        "modal_title": "Eliminar cuenta: ",
        "modal_description": "Eliminar cuenta: ",
        "cancel_url": success_url
    }
    success_message = "Cuenta object eliminada exitosamente"


class WhatsAppDistributionListsListView(ListView):
    template_name = 'whatsapp/distribucion_lists/index.html'
    queryset = models.WhatsAppDistributionList.objects.all()


class WhatsAppDistributionListsCreateView(SuccessMessageMixin, CreateView):
    # success_url = reverse_lazy('whatsapp:distribution-lists.update')
    form_class = forms.WhatsAppDistributionListCreateForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nueva lista de distribución",
        "cancel_url": reverse_lazy('whatsapp:distribution-lists.index')
    }
    success_message = "Lista de distribución creada exitosamente"

    def get_success_url(self):
        return str(reverse_lazy('whatsapp:distribution-lists.update', kwargs=dict(pk=self.object.pk)))


class WhatsAppDistributionListsUpdateView(SuccessMessageMixin, UpdateView):
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    form_class = forms.WhatsAppDistributionListUpdateForm
    queryset = models.WhatsAppDistributionList.objects.all()
    template_name = 'whatsapp/distribucion_lists/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar lista de distribución: ",
        "cancel_url": success_url
    }
    success_message = "Lista de distribución {name} actualizada exitosamente"


class WhatsAppDistributionListsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    queryset = models.WhatsAppDistributionList.objects.all()
    success_message = "Lista de distribución object activada/desactivada exitosamente"


class WhatsAppDistributionListsDeleteView(SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    queryset = models.WhatsAppDistributionList.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar lista de distribución: ",
        "modal_title": "Eliminar lista de distribución: ",
        "modal_description": "Eliminar lista de distribución",
        "cancel_url": success_url
    }
    success_message = "Lista de distribución object eliminada exitosamente"


class WhatsAppMessagesListView(FilterView):
    template_name = 'whatsapp/messages/index.html'
    queryset = models.WhatsAppMessage.objects.all()
    filterset_class = filters.WhatsAppMessagesFilterSet


class WhatsAppMessageCreateView(SuccessMessageMixin, CreateView):
    success_url = reverse_lazy('whatsapp:messages.index')
    form_class = forms.WhatsAppMessageForm
    template_name = 'whatsapp/messages/create_or_update.html'
    extra_context = {
        "page_title": "Crear un nuevo mensaje",
        "cancel_url": success_url
    }
    success_message = "Nuevo mensaje creado exitosamente"


class WhatsAppMessageUpdateView(SuccessMessageMixin, UpdateView):
    success_url = reverse_lazy('whatsapp:messages.index')
    form_class = forms.WhatsAppMessageForm
    queryset = models.WhatsAppMessage.objects.all()
    template_name = 'whatsapp/messages/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar mensaje: ",
        "cancel_url": success_url
    }
    success_message = "Mensaje {name} actualizado exitosamente"


class WhatsAppMessageDeleteView(SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy('whatsapp:messages.index')
    queryset = models.WhatsAppMessage.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar mensaje: ",
        "modal_title": "Eliminar mensaje: ",
        "modal_description": "Eliminar mensaje",
        "cancel_url": success_url
    }
    success_message = "Mensaje {name} eliminado exitosamente"


class WhatsAppMessageToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:messages.index')
    queryset = models.WhatsAppMessage.objects.all()
    success_message = "Mensaje {name} activado/desactivado exitosamente"


class WhatsAppAccountDetailView(DetailView):
    queryset = models.WhatsAppAccount.objects.all()
    template_name = 'whatsapp/accounts/details.html'

    def get_context_data(self, **kwargs):
        last_messages = self.get_object().messages.filter(published_count__gt=0).order_by('-updated_at')[:10]
        last_statues = self.get_object().status.filter(published_count__gt=0).order_by('-updated_at')[:10]
        return super().get_context_data(last_messages=last_messages, last_statues=last_statues, **kwargs)


class WhatsAppAccountSynchronizeGroupsView(SuccessMessageMixin, SingleFormView):
    queryset = models.WhatsAppAccount.objects.all()
    success_message = "Grupos actualizados correctamente"

    def form_valid(self, form):
        syncronize_whatsapp_account_groups(self.get_object())
        return super().form_valid(form)

    def get_success_url(self):
        return str(reverse_lazy('whatsapp:accounts.details', kwargs=dict(pk=self.get_object().pk)))


class WhatsAppAccountSynchronizeContactsView(SuccessMessageMixin, SingleFormView):
    queryset = models.WhatsAppAccount.objects.all()
    success_message = "Contactos actualizados correctamente"

    def form_valid(self, form):
        syncronize_whatsapp_account_contacts(self.get_object())
        return super().form_valid(form)

    def get_success_url(self):
        return str(reverse_lazy('whatsapp:accounts.details', kwargs=dict(pk=self.get_object().pk)))


class WhatsAppMessagesSorterView(SuccessMessageMixin, FormView):
    success_message = "Mensajes ordenados correctamente."
    template_name = 'whatsapp/messages/sort.html'
    form_class = forms.WhatAppSortMessageFormSet

    def dispatch(self, request, *args, **kwargs):
        self.account = get_object_or_404(models.WhatsAppAccount, id=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.account.messages.all()

    def get_context_data(self, **kwargs):
        return super().get_context_data(object_list=self.get_queryset(), **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            return {'data': self.request.POST, 'queryset': self.get_queryset(), **kwargs}
        return {'queryset': self.get_queryset(), **kwargs}

    def form_valid(self, formset):
        for form in formset.ordered_forms:
            instance = form.save(commit=False)
            instance.order = form.cleaned_data['ORDER']
            instance.save()
        return super().form_valid(formset)

    def get_success_url(self):
        return reverse('whatsapp:accounts.sort-messages', kwargs={'pk': self.account.pk})


class WhatsAppStatusSorterView(WhatsAppMessagesSorterView):
    success_message = "Estados ordenados correctamente"
    template_name = "whatsapp/status/sort.html"
    form_class = forms.WhatAppSortStatusFormSet

    def get_queryset(self):
        return self.account.status.all()

    def get_success_url(self):
        return reverse('whatsapp:accounts.sort-status', kwargs={'pk': self.account.pk})


class PublishNowWhatsAppStatusView(SuccessMessageMixin, FilterView, FormView):
    filterset_class = filters.WhatsAppStatusFilterSet
    form_class = forms.PublishWhastAppStatusForm
    queryset = models.WhatsAppStatus.objects.all()
    success_message = "Estados enviados a publicar correctamente"
    success_url = reverse_lazy('whatsapp:status.index')

    def form_valid(self, form):
        form.publish()
        return super().form_valid(form)


class PublishNowWhatsAppMessagesView(PublishNowWhatsAppStatusView):
    filterset_class = filters.WhatsAppMessagesFilterSet
    form_class = forms.PublishWhastAppMessagesForm
    queryset = models.WhatsAppMessage.objects.all()
    template_name = 'whatsapp/messages/publish_now.html'
    success_message = "Mensajes enviados a publicar correctamente"
    success_url = reverse_lazy('whatsapp:messages.index')
