from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.timezone import localtime
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django_filters.views import FilterView

from core.generics import ToggleStatusView, SingleFormView, DuplicateView
from core.models import Schedule
from whatsapp import filters
from whatsapp import models, forms
from whatsapp.mixins import WhatsAppAccountViewMixins, FilterByAccountViewMixins
from whatsapp.models import WhatsAppScheduleMessage
from whatsapp.tasks import syncronize_whatsapp_account_groups, syncronize_whatsapp_account_contacts


class WhatsAppStatusListView(FilterByAccountViewMixins, FilterView):
    template_name = 'whatsapp/status/index.html'
    filterset_class = filters.WhatsAppStatusFilterSet
    queryset = models.WhatsAppStatus.objects.all()
    paginate_by = 100


class WhatsAppStatusCreateView(SuccessMessageMixin, CreateView):
    success_url = reverse_lazy('whatsapp:status.index')
    form_class = forms.WhatsAppStatusForm
    template_name = 'whatsapp/status/create_or_update.html'
    success_message = 'Nuevo estado  %(name)s creado exitosamente.'
    extra_context = {
        "page_title": "Crear nuevo estado",
        "cancel_url": success_url
    }


class WhatsAppStatusUpdateView(SuccessMessageMixin, FilterByAccountViewMixins, UpdateView):
    success_url = reverse_lazy('whatsapp:status.index')
    form_class = forms.WhatsAppStatusForm
    queryset = models.WhatsAppStatus.objects.all()
    template_name = 'whatsapp/status/create_or_update.html'
    success_message = 'Estado %(name)s actualizado exitosamente.'
    extra_context = {
        "page_title": "Actualizar estado: ",
        "cancel_url": success_url
    }


class WhatsAppStatusToggleStatusView(SuccessMessageMixin, FilterByAccountViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:status.index')
    queryset = models.WhatsAppStatus.objects.all()

    def get_success_message(self, cleaned_data):
        return f"Estado {self.get_object()} activado/desactivado exitosamente"


class WhatsAppContactsListView(FilterByAccountViewMixins, FilterView):
    template_name = 'whatsapp/contacts/index.html'
    filterset_class = filters.WhatsAppContactsFilterSet
    queryset = models.WhatsAppContact.objects.all()
    paginate_by = 100


class WhatsAppContactsUpdateView(SuccessMessageMixin, FilterByAccountViewMixins, UpdateView):
    success_url = reverse_lazy('whatsapp:contacts.index')
    template_name = 'whatsapp/contacts/create_or_update.html'
    form_class = forms.WhatsAppContactForm
    queryset = models.WhatsAppContact.objects.all()
    success_message = "Contacto %(name)s actualizado exitosamente"
    extra_context = {
        "page_title": "Actualizar contacto: ",
        "cancel_url": success_url
    }


class WhatsAppContactsDeleteView(SuccessMessageMixin, FilterByAccountViewMixins, DeleteView):
    success_url = reverse_lazy('whatsapp:contacts.index')
    queryset = models.WhatsAppContact.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar contacto: ",
        "modal_title": "Eliminar contacto: ",
        "modal_description": "Eliminar contacto",
        "cancel_url": success_url
    }

    def get_success_message(self, cleaned_data):
        return f"Contacto {self.object} eliminado exitosamente"


class WhatsAppContactsToggleStatusView(SuccessMessageMixin, FilterByAccountViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:contacts.index')
    queryset = models.WhatsAppContact.objects.all()

    def get_success_message(self, cleaned_data):
        return f"Contacto {self.get_object()} activado/desactivado exitosamente"


class WhatsAppGroupsListView(FilterByAccountViewMixins, FilterView):
    template_name = 'whatsapp/groups/index.html'
    filterset_class = filters.WhatsAppGroupsFilterSet
    queryset = models.WhatsAppGroup.objects.all()
    paginate_by = 100


class WhatsAppGroupsToggleStatusView(SuccessMessageMixin, FilterByAccountViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:groups.index')
    queryset = models.WhatsAppGroup.objects.all()

    def get_success_message(self, cleaned_data):
        return f"Grupo {self.get_object()} activado/desactivado exitosamente"


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
    success_message = "Cuenta %(name)s creada exitosamente"


class WhatsAppAccountsUpdateView(WhatsAppAccountViewMixins, SuccessMessageMixin, UpdateView):
    success_url = reverse_lazy('whatsapp:accounts.index')
    form_class = forms.WhatsAppUpdateAccountForm
    template_name = 'whatsapp/accounts/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar cuenta: ",
        "cancel_url": success_url
    }
    success_message = "Cuenta %(name)s actualizada exitosamente"


class WhatsAppAccountsToggleStatusView(WhatsAppAccountViewMixins, SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:accounts.index')

    def get_success_message(self, cleaned_data):
        return f"Cuenta {self.get_object()} activada/desactivada exitosamente"


class WhatsAppAccountsDeleteView(SuccessMessageMixin, WhatsAppAccountViewMixins, DeleteView):
    success_url = reverse_lazy('whatsapp:accounts.index')
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar cuenta: ",
        "modal_title": "Eliminar cuenta: ",
        "modal_description": "Eliminar cuenta: ",
        "cancel_url": success_url
    }

    def get_success_message(self, cleaned_data):
        return f"Cuenta {self.object} eliminada exitosamente"


class WhatsAppDistributionListsListView(FilterByAccountViewMixins, ListView):
    template_name = 'whatsapp/distribucion_lists/index.html'
    queryset = models.WhatsAppDistributionList.objects.all()


class WhatsAppDistributionListsCreateView(SuccessMessageMixin, FilterByAccountViewMixins, CreateView):
    # success_url = reverse_lazy('whatsapp:distribution-lists.update')
    form_class = forms.WhatsAppDistributionListCreateForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nueva lista de distribución",
        "cancel_url": reverse_lazy('whatsapp:distribution-lists.index')
    }
    success_message = "Lista de distribución %(name)s creada exitosamente"

    def get_success_url(self):
        return str(reverse_lazy('whatsapp:distribution-lists.update', kwargs=dict(pk=self.object.pk)))


class WhatsAppDistributionListsUpdateView(SuccessMessageMixin, FilterByAccountViewMixins, UpdateView):
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    form_class = forms.WhatsAppDistributionListUpdateForm
    queryset = models.WhatsAppDistributionList.objects.all()
    template_name = 'whatsapp/distribucion_lists/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar lista de distribución: ",
        "cancel_url": success_url
    }
    success_message = "Lista de distribución %(name)s actualizada exitosamente"


class WhatsAppDistributionListsToggleStatusView(SuccessMessageMixin, FilterByAccountViewMixins,
                                                ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    queryset = models.WhatsAppDistributionList.objects.all()

    def get_success_message(self, cleaned_data):
        return f"Lista de distribución {self.get_object()} activada/desactivada exitosamente"


class WhatsAppDistributionListsDeleteView(SuccessMessageMixin, FilterByAccountViewMixins, DeleteView):
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    template_name = 'layout/admin_delete_layout.html'
    queryset = models.WhatsAppDistributionList.objects.all()
    extra_context = {
        "page_title": "Eliminar lista de distribución: ",
        "modal_title": "Eliminar lista de distribución: ",
        "modal_description": "Eliminar lista de distribución",
        "cancel_url": success_url
    }

    def get_success_message(self, cleaned_data):
        return f"Lista de distribución {self.object} eliminada exitosamente"


class WhatsAppMessagesListView(FilterByAccountViewMixins, FilterView):
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
    success_message = "Nuevo mensaje %(name)s creado exitosamente"


class WhatsAppMessageUpdateView(SuccessMessageMixin, FilterByAccountViewMixins, UpdateView):
    success_url = reverse_lazy('whatsapp:messages.index')
    form_class = forms.WhatsAppMessageForm
    queryset = models.WhatsAppMessage.objects.all()
    template_name = 'whatsapp/messages/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar mensaje: ",
        "cancel_url": success_url
    }
    success_message = "Mensaje %(name)s actualizado exitosamente"

    def get_initial(self):
        schedules = Schedule.objects.filter(messages__message=self.get_object()).order_by('time').all()
        return {'schedules': schedules, **super().get_initial()}


class WhatsAppMessageDeleteView(SuccessMessageMixin, FilterByAccountViewMixins, DeleteView):
    success_url = reverse_lazy('whatsapp:messages.index')
    queryset = models.WhatsAppMessage.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar mensaje: ",
        "modal_title": "Eliminar mensaje: ",
        "modal_description": "Eliminar mensaje",
        "cancel_url": success_url
    }

    def get_success_message(self, cleaned_data):
        return f"Mensaje {self.object} eliminado exitosamente"


class WhatsAppMessageToggleStatusView(SuccessMessageMixin, FilterByAccountViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:messages.index')
    queryset = models.WhatsAppMessage.objects.all()

    def get_success_message(self, cleaned_data):
        return f"Mensaje {self.get_object()} activado/desactivado exitosamente"


class WhatsAppAccountDetailView(WhatsAppAccountViewMixins, DetailView):
    template_name = 'whatsapp/accounts/details.html'

    def get_context_data(self, **kwargs):
        last_messages = self.get_object().messages.filter(published_count__gt=0).order_by('-updated_at')[:10]
        last_statues = self.get_object().status.filter(published_count__gt=0).order_by('-updated_at')[:10]
        return super().get_context_data(last_messages=last_messages, last_statues=last_statues, **kwargs)


class WhatsAppAccountSynchronizeGroupsView(SuccessMessageMixin, WhatsAppAccountViewMixins, SingleFormView):
    def form_valid(self, form):
        syncronize_whatsapp_account_groups(self.get_object())
        return super().form_valid(form)

    def get_success_url(self):
        return str(reverse_lazy('whatsapp:accounts.details', kwargs=dict(pk=self.get_object().pk)))

    def get_success_message(self, cleaned_data):
        return f"Grupos de {self.get_object()} actualizados correctamente"


class WhatsAppAccountSynchronizeContactsView(SuccessMessageMixin, WhatsAppAccountViewMixins, SingleFormView):

    def form_valid(self, form):
        syncronize_whatsapp_account_contacts(self.get_object())
        return super().form_valid(form)

    def get_success_url(self):
        return str(reverse_lazy('whatsapp:accounts.details', kwargs=dict(pk=self.get_object().pk)))

    def get_success_message(self, cleaned_data):
        return f"Contactos de {self.get_object()} actualizados correctamente"


class WhatsAppMessagesSorterView(SuccessMessageMixin, FormView):
    template_name = 'whatsapp/messages/sort.html'
    form_class = forms.WhatAppSortMessageFormSet

    def dispatch(self, request, *args, **kwargs):
        self.account = get_object_or_404(models.WhatsAppAccount, id=self.kwargs['pk'])
        self.schedule = get_object_or_404(Schedule, pk=self.kwargs['schedule_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        current_time = localtime()
        return (WhatsAppScheduleMessage.objects
                .filter(schedule=self.schedule, message__account=self.account)
                .filter(message__from_date__lte=current_time)
                .filter(Q(message__until_date__gte=current_time) | Q(message__until_date__isnull=True))
                .order_by('order').all())

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

    def get_success_message(self, cleaned_data):
        return f"Mensajes de {self.account} organizados correctamente en el horario {self.schedule}"


# TODO REVISAR ESTE ELEMENTO
class WhatsAppStatusSorterView(SuccessMessageMixin, FormView):
    template_name = "whatsapp/status/sort.html"
    form_class = forms.WhatAppSortStatusFormSet

    def dispatch(self, request, *args, **kwargs):
        self.account = get_object_or_404(models.WhatsAppAccount, id=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        current_time = localtime()
        return (self.account.status.filter(from_date__lte=current_time)
                .filter(Q(until_date__gte=current_time) | Q(until_date__isnull=True)).all())

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

    def get_success_message(self, cleaned_data):
        return f"Estados de {self.account} organizados correctamente"


class PublishNowWhatsAppStatusView(SuccessMessageMixin, FilterByAccountViewMixins, FilterView, FormView):
    filterset_class = filters.WhatsAppStatusFilterSet
    form_class = forms.PublishWhastAppStatusForm
    template_name = 'whatsapp/status/publish_now.html'
    success_message = "Estados enviados a publicar correctamente"
    success_url = reverse_lazy('whatsapp:status.index')
    queryset = models.WhatsAppStatus.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(active=True).all()

    def form_valid(self, form):
        form.publish()
        return super().form_valid(form)


class PublishNowWhatsAppMessagesView(PublishNowWhatsAppStatusView):
    filterset_class = filters.WhatsAppMessagesFilterSet
    form_class = forms.PublishWhastAppMessagesForm
    template_name = 'whatsapp/messages/publish_now.html'
    success_message = "Mensajes enviados a publicar correctamente"
    success_url = reverse_lazy('whatsapp:messages.index')
    queryset = models.WhatsAppMessage.objects.all()


class WhatsAppStatusDuplicateView(FilterByAccountViewMixins, DuplicateView):
    success_url = reverse_lazy('whatsapp:status.index')
    queryset = models.WhatsAppStatus.objects.all()
    template_name = 'whatsapp/status/duplicate.html'

    def duplicate_object(self):
        old_object = self.get_object()
        self.object.whatsapp_last_id = None
        super().duplicate_object()
        self.object.weekdays.set(old_object.weekdays.all())

    def get_success_message(self, cleaned_data):
        return f"Estado {self.get_object()} duplicado correctamente"


class WhatsAppMessageDuplicateView(FilterByAccountViewMixins, DuplicateView):
    success_url = reverse_lazy('whatsapp:messages.index')
    queryset = models.WhatsAppMessage.objects.all()
    template_name = 'whatsapp/messages/duplicate.html'

    def duplicate_object(self):
        old_object = self.get_object()
        self.object.whatsapp_last_id = None
        super().duplicate_object()
        self.object.distribution_lists.set(old_object.distribution_lists.all())
        self.object.weekdays.set(old_object.weekdays.all())

        schedules = Schedule.objects.filter(messages__message=old_object).all()
        for schedule in schedules:
            last_order = (WhatsAppScheduleMessage.objects
                          .filter(schedule=schedule, message__account=self.object.account)
                          .aggregate(Max("order"))["order__max"] or 0)
            WhatsAppScheduleMessage.objects.create(schedule=schedule, message=self.object, order=last_order)

    def get_success_message(self, cleaned_data):
        return f"Mensaje {self.get_object()} duplicado correctamente"


class WhatsAppAccountScheduleDetailView(WhatsAppAccountViewMixins, DetailView):
    queryset = models.WhatsAppAccount.objects.all()
    template_name = 'whatsapp/accounts/schedules/index.html'
    context_object_name = 'account'

    def get_context_data(self, **kwargs):
        schedules = Schedule.objects.filter(messages__message__account=self.get_object()).order_by('time').distinct()
        return super().get_context_data(object_list=schedules, **kwargs)


class WhatsAppAccountJoinGroupsView(SuccessMessageMixin, FormView):
    template_name = 'whatsapp/groups/join.html'
    form_class = forms.WhatsAppAccountJoinGroupForm
    success_url = reverse_lazy('whatsapp:groups.index')

    def form_valid(self, form):
        try:
            instance = form.save()
            self.success_message = f"La cuenta {form.cleaned_data['account']} se ha unido correctamente al grupo {instance}"
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, "Ha ocurrido un error al intentar unise al grupo")
            return self.form_invalid(form)
