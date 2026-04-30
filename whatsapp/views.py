from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django_filters.views import FilterView

from core.generics import ToggleStatusView, SingleFormView, DuplicateView
from core.models import Schedule
from whatsapp import filters
from whatsapp import models, forms
from whatsapp.mixins import WhatsAppAccountViewMixins, WhatsAppStatusViewMixins, WhatsAppContactViewMixins, \
    WhatsAppGroupViewMixins, WhatsAppDistributionListViewMixins, WhatsAppMessageViewMixins
from whatsapp.models import WhatsAppScheduleMessage
from whatsapp.tasks import syncronize_whatsapp_account_groups, syncronize_whatsapp_account_contacts


class WhatsAppStatusListView(WhatsAppStatusViewMixins, FilterView):
    template_name = 'whatsapp/status/index.html'
    filterset_class = filters.WhatsAppStatusFilterSet
    paginate_by = 100


class WhatsAppStatusCreateView(CreateView):
    success_url = reverse_lazy('whatsapp:status.index')
    form_class = forms.WhatsAppStatusForm
    template_name = 'whatsapp/status/create_or_update.html'
    extra_context = {
        "page_title": "Crear nuevo estado",
        "cancel_url": success_url
    }


class WhatsAppStatusUpdateView(WhatsAppStatusViewMixins, UpdateView):
    success_url = reverse_lazy('whatsapp:status.index')
    form_class = forms.WhatsAppStatusForm
    template_name = 'whatsapp/status/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar estado: ",
        "cancel_url": success_url
    }


class WhatsAppStatusToggleStatusView(SuccessMessageMixin, WhatsAppStatusViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:status.index')
    queryset = models.WhatsAppStatus.objects.all()
    success_message = "Estado object activado/desactivado exitosamente"


class WhatsAppContactsListView(WhatsAppContactViewMixins, FilterView):
    template_name = 'whatsapp/contacts/index.html'
    filterset_class = filters.WhatsAppContactsFilterSet
    queryset = models.WhatsAppContact.objects.all()
    paginate_by = 100


class WhatsAppContactsUpdateView(WhatsAppContactViewMixins, UpdateView):
    success_url = reverse_lazy('whatsapp:contacts.index')
    template_name = 'whatsapp/contacts/create_or_update.html'
    form_class = forms.WhatsAppContactForm
    extra_context = {
        "page_title": "Actualizar contacto: ",
        "cancel_url": success_url
    }


class WhatsAppContactsDeleteView(SuccessMessageMixin, WhatsAppContactViewMixins, DeleteView):
    success_url = reverse_lazy('whatsapp:contacts.index')
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar contacto: ",
        "modal_title": "Eliminar contacto: ",
        "modal_description": "Eliminar contacto",
        "cancel_url": success_url
    }
    success_message = "Contacto {object} eliminada exitosamente"


class WhatsAppContactsToggleStatusView(SuccessMessageMixin, WhatsAppContactViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:contacts.index')
    success_message = "Contacto object activado/desactivado exitosamente"


class WhatsAppGroupsListView(WhatsAppGroupViewMixins, FilterView):
    template_name = 'whatsapp/groups/index.html'
    filterset_class = filters.WhatsAppGroupsFilterSet
    paginate_by = 100


class WhatsAppGroupsToggleStatusView(SuccessMessageMixin, WhatsAppGroupViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:groups.index')
    success_message = "Grupo object activado/desactivado exitosamente"


class WhatsAppAccountsListView(WhatsAppAccountViewMixins, ListView, LoginRequiredMixin):
    template_name = 'whatsapp/accounts/index.html'


class WhatsAppAccountsCreateView(SuccessMessageMixin, CreateView):
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
    template_name = 'whatsapp/accounts/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar cuenta: ",
        "cancel_url": success_url
    }
    success_message = "Cuenta object actualizada exitosamente"


class WhatsAppAccountsToggleStatusView(WhatsAppAccountViewMixins, SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:accounts.index')
    success_message = "Cuenta object activada/desactivada exitosamente"


class WhatsAppAccountsDeleteView(SuccessMessageMixin, WhatsAppAccountViewMixins, DeleteView):
    success_url = reverse_lazy('whatsapp:accounts.index')
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar cuenta: ",
        "modal_title": "Eliminar cuenta: ",
        "modal_description": "Eliminar cuenta: ",
        "cancel_url": success_url
    }
    success_message = "Cuenta object eliminada exitosamente"


class WhatsAppDistributionListsListView(WhatsAppDistributionListViewMixins, ListView):
    template_name = 'whatsapp/distribucion_lists/index.html'


class WhatsAppDistributionListsCreateView(SuccessMessageMixin, WhatsAppDistributionListViewMixins, CreateView):
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


class WhatsAppDistributionListsUpdateView(SuccessMessageMixin, WhatsAppDistributionListViewMixins, UpdateView):
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    form_class = forms.WhatsAppDistributionListUpdateForm
    template_name = 'whatsapp/distribucion_lists/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar lista de distribución: ",
        "cancel_url": success_url
    }
    success_message = "Lista de distribución {name} actualizada exitosamente"


class WhatsAppDistributionListsToggleStatusView(SuccessMessageMixin, WhatsAppDistributionListViewMixins,
                                                ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    success_message = "Lista de distribución object activada/desactivada exitosamente"


class WhatsAppDistributionListsDeleteView(SuccessMessageMixin, WhatsAppDistributionListViewMixins, DeleteView):
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar lista de distribución: ",
        "modal_title": "Eliminar lista de distribución: ",
        "modal_description": "Eliminar lista de distribución",
        "cancel_url": success_url
    }
    success_message = "Lista de distribución object eliminada exitosamente"


class WhatsAppMessagesListView(WhatsAppMessageViewMixins, FilterView):
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


class WhatsAppMessageUpdateView(SuccessMessageMixin, WhatsAppMessageViewMixins, UpdateView):
    success_url = reverse_lazy('whatsapp:messages.index')
    form_class = forms.WhatsAppMessageForm
    queryset = models.WhatsAppMessage.objects.all()
    template_name = 'whatsapp/messages/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar mensaje: ",
        "cancel_url": success_url
    }
    success_message = "Mensaje {name} actualizado exitosamente"

    def get_initial(self):
        schedules = Schedule.objects.filter(messages__message=self.get_object()).order_by('time').all()
        return {'schedules': schedules, **super().get_initial()}


class WhatsAppMessageDeleteView(SuccessMessageMixin, WhatsAppMessageViewMixins, DeleteView):
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


class WhatsAppMessageToggleStatusView(SuccessMessageMixin, WhatsAppMessageViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:messages.index')
    queryset = models.WhatsAppMessage.objects.all()
    success_message = "Mensaje {name} activado/desactivado exitosamente"


class WhatsAppAccountDetailView(WhatsAppAccountViewMixins, DetailView):
    template_name = 'whatsapp/accounts/details.html'

    def get_context_data(self, **kwargs):
        last_messages = self.get_object().messages.filter(published_count__gt=0).order_by('-updated_at')[:10]
        last_statues = self.get_object().status.filter(published_count__gt=0).order_by('-updated_at')[:10]
        return super().get_context_data(last_messages=last_messages, last_statues=last_statues, **kwargs)


class WhatsAppAccountSynchronizeGroupsView(SuccessMessageMixin, WhatsAppAccountViewMixins, SingleFormView):
    success_message = "Grupos actualizados correctamente"

    def form_valid(self, form):
        syncronize_whatsapp_account_groups(self.get_object())
        return super().form_valid(form)

    def get_success_url(self):
        return str(reverse_lazy('whatsapp:accounts.details', kwargs=dict(pk=self.get_object().pk)))


class WhatsAppAccountSynchronizeContactsView(SuccessMessageMixin, WhatsAppAccountViewMixins, SingleFormView):
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
        self.schedule = get_object_or_404(Schedule, pk=self.kwargs['schedule_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # TODO REVISAR ESTE QUERYSET
        return WhatsAppScheduleMessage.objects \
            .filter(schedule=self.schedule, message__account=self.account).order_by('order').all()

    def get_context_data(self, **kwargs):
        return super().get_context_data(object_list=self.get_queryset(), account=self.account, schedule=self.schedule,
                                        **kwargs)

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
        return reverse('whatsapp:accounts.sort-messages',
                       kwargs={'pk': self.account.pk, 'schedule_pk': self.schedule.pk})


# TODO REVISAR ESTE ELEMENTO
class WhatsAppStatusSorterView(SuccessMessageMixin, FormView):
    success_message = "Estados ordenados correctamente"
    template_name = "whatsapp/status/sort.html"
    form_class = forms.WhatAppSortStatusFormSet

    def dispatch(self, request, *args, **kwargs):
        self.account = get_object_or_404(models.WhatsAppAccount, id=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.account.status.all()

    def get_context_data(self, **kwargs):
        return super().get_context_data(object_list=self.get_queryset(), account=self.account, **kwargs)

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
        return reverse('whatsapp:accounts.sort-status', kwargs={'pk': self.account.pk})


class PublishNowWhatsAppStatusView(SuccessMessageMixin, WhatsAppStatusViewMixins, FilterView, FormView):
    filterset_class = filters.WhatsAppStatusFilterSet
    form_class = forms.PublishWhastAppStatusForm
    template_name = 'whatsapp/status/publish_now.html'
    success_message = "Estados enviados a publicar correctamente"
    success_url = reverse_lazy('whatsapp:status.index')

    def get_queryset(self):
        return super().get_queryset().filter(active=True).all()

    def form_valid(self, form):
        form.publish()
        return super().form_valid(form)


class PublishNowWhatsAppMessagesView(WhatsAppMessageViewMixins, PublishNowWhatsAppStatusView):
    filterset_class = filters.WhatsAppMessagesFilterSet
    form_class = forms.PublishWhastAppMessagesForm
    template_name = 'whatsapp/messages/publish_now.html'
    success_message = "Mensajes enviados a publicar correctamente"
    success_url = reverse_lazy('whatsapp:messages.index')

    def get_queryset(self):
        return super().get_queryset().filter(active=True).all()


class WhatsAppStatusDuplicateView(WhatsAppStatusViewMixins, DuplicateView):
    success_url = reverse_lazy('whatsapp:status.index')
    success_message = "Estado duplicado correctamente correctamente"
    template_name = 'whatsapp/status/duplicate.html'


class WhatsAppMessageDuplicateView(WhatsAppMessageViewMixins, DuplicateView):
    success_url = reverse_lazy('whatsapp:messages.index')
    success_message = "Estado duplicado correctamente correctamente"
    template_name = 'whatsapp/messages/duplicate.html'


class WhatsAppAccountScheduleDetailView(DetailView):
    queryset = models.WhatsAppAccount.objects.all()
    template_name = 'whatsapp/accounts/schedules/index.html'
    context_object_name = 'account'

    def get_context_data(self, **kwargs):
        schedules = Schedule.objects.filter(messages__message__account=self.get_object()).order_by('time').distinct()
        return super().get_context_data(object_list=schedules, **kwargs)
