from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django_filters.views import FilterView

from whatsapp import filters
from whatsapp import models, forms


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
        "page_title": "Crear nuevo estado"
    }


class WhatsAppStatusUpdateView(UpdateView):
    success_url = reverse_lazy('whatsapp:status.index')
    form_class = forms.WhatsAppStatusForm
    queryset = models.WhatsAppStatus.objects.all()
    template_name = 'whatsapp/status/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar {{instance}}"
    }


class WhatsAppContactsListView(FilterView):
    template_name = 'whatsapp/contacts/index.html'
    filterset_class = filters.WhatsAppGenericFilterSet
    queryset = models.WhatsAppContact.objects.all()
    paginate_by = 100


class WhatsAppContactsUpdateView(UpdateView):
    template_name = 'whatsapp/contacts/create_or_update.html'
    form_class = forms.WhatsAppContactForm
    queryset = models.WhatsAppContact.objects.all()
    extra_context = {
        "page_title": "Actualizar contacto"
    }


class WhatsAppGroupsListView(FilterView):
    template_name = 'whatsapp/groups/index.html'
    filterset_class = filters.WhatsAppGenericFilterSet
    queryset = models.WhatsAppGroup.objects.all()
    paginate_by = 100
