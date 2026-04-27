from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django_filters.views import FilterView

from core.generics import ToggleStatusView
from facebook import forms, filters
from facebook import models


class FacebookAccountsListView(ListView):
    template_name = 'facebook/accounts/index.html'
    queryset = models.FacebookProfile.objects.all()


class FacebookAccountDetailView(DetailView):
    queryset = models.FacebookProfile.objects.all()
    template_name = 'whatsapp/accounts/details.html'


class FacebookAccountsCreateView(SuccessMessageMixin, CreateView):
    success_url = reverse_lazy('facebook:accounts.index')
    form_class = forms.FacebookAccountForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nueva cuenta",
        "cancel_url": success_url
    }
    success_message = "Cuenta creada exitosamente"


class FacebookAccountsUpdateView(SuccessMessageMixin, UpdateView):
    success_url = reverse_lazy('facebook:accounts.index')
    form_class = forms.FacebookAccountForm
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


class FacebookGroupsListView(FilterView):
    template_name = 'facebook/groups/index.html'
    filterset_class = filters.FacebookGroupsFilterSet
    queryset = models.FacebookGroup.objects.all()
    paginate_by = 100


class FacebookGroupsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:groups.index')
    queryset = models.FacebookGroup.objects.all()
    success_message = "Grupo object activado/desactivado exitosamente"


class FacebookAgentListView(ListView):
    template_name = 'facebook/agents/index.html'
    queryset = models.FacebookLeadExplorer.objects.all()


class FacebookAgentDetailView(DetailView):
    queryset = models.FacebookLeadExplorer.objects.all()
    template_name = 'whatsapp/accounts/details.html'


class FacebookAgentCreateView(SuccessMessageMixin, CreateView):
    success_url = reverse_lazy('facebook:agents.index')
    form_class = forms.FacebookAgentForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nuevo agente",
        "cancel_url": success_url
    }
    success_message = "Agente creado exitosamente"


class FacebookAgentUpdateView(SuccessMessageMixin, UpdateView):
    success_url = reverse_lazy('facebook:agents.index')
    form_class = forms.FacebookAgentForm
    queryset = models.FacebookLeadExplorer.objects.all()
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Actualizar agente: ",
        "cancel_url": success_url
    }
    success_message = "Agente object actualizado exitosamente"


class FacebookAgentToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:agents.index')
    queryset = models.FacebookLeadExplorer.objects.all()
    success_message = "Agente object activada/desactivada exitosamente"
