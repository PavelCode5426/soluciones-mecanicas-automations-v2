from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django_filters.views import FilterView

from core.generics import ToggleStatusView, DuplicateView
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
    queryset = models.FacebookAgent.objects.all()


class FacebookAgentDetailView(DetailView):
    queryset = models.FacebookAgent.objects.all()
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
    queryset = models.FacebookAgent.objects.all()
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Actualizar agente: ",
        "cancel_url": success_url
    }
    success_message = "Agente object actualizado exitosamente"


class FacebookAgentToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:agents.index')
    queryset = models.FacebookAgent.objects.all()
    success_message = "Agente object activada/desactivada exitosamente"


class FacebookDistributionListsListView(ListView):
    template_name = 'facebook/distribucion_lists/index.html'
    queryset = models.FacebookDistributionList.objects.all()


class FacebookDistributionListsCreateView(SuccessMessageMixin, CreateView):
    # success_url = reverse_lazy('whatsapp:distribution-lists.update')
    form_class = forms.FacebookDistributionListCreateForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nueva lista de distribución",
        "cancel_url": reverse_lazy('whatsapp:distribution-lists.index')
    }
    success_message = "Lista de distribución creada exitosamente"

    def get_success_url(self):
        return str(reverse_lazy('facebook:distribution-lists.update', kwargs=dict(pk=self.object.pk)))


class FacebookDistributionListsUpdateView(SuccessMessageMixin, UpdateView):
    success_url = reverse_lazy('facebook:distribution-lists.index')
    form_class = forms.FacebookDistributionListUpdateForm
    queryset = models.FacebookDistributionList.objects.all()
    template_name = 'facebook/distribucion_lists/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar lista de distribución: ",
        "cancel_url": success_url
    }
    success_message = "Lista de distribución {name} actualizada exitosamente"


class FacebookDistributionListsToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    queryset = models.FacebookDistributionList.objects.all()
    success_message = "Lista de distribución object activada/desactivada exitosamente"


class FacebookDistributionListsDeleteView(SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy('whatsapp:distribution-lists.index')
    queryset = models.FacebookDistributionList.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar lista de distribución: ",
        "modal_title": "Eliminar lista de distribución: ",
        "modal_description": "Eliminar lista de distribución",
        "cancel_url": success_url
    }
    success_message = "Lista de distribución object eliminada exitosamente"


class FacebookPostCampaignListView(FilterView):
    template_name = 'facebook/post_campaings/index.html'
    queryset = models.FacebookPostCampaign.objects.all()
    filterset_class = filters.FacebookPostCampaingFilterSet


class FacebookPostCampaignCreateView(SuccessMessageMixin, CreateView):
    success_url = reverse_lazy('facebook:post-campaign.index')
    form_class = forms.FacebookPostCampaignForm
    template_name = 'facebook/post_campaings/create_or_update.html'
    extra_context = {
        "page_title": "Crear un nuevo mensaje",
        "cancel_url": success_url
    }
    success_message = "Nueva campaña creada exitosamente"


class FacebookPostCampaignUpdateView(SuccessMessageMixin, UpdateView):
    success_url = reverse_lazy('facebook:post-campaign.index')
    form_class = forms.FacebookPostCampaignForm
    queryset = models.FacebookPostCampaign.objects.all()
    template_name = 'facebook/post_campaings/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar campaña: ",
        "cancel_url": success_url
    }
    success_message = "Mensaje {name} actualizado exitosamente"


class FacebookPostCampaignDeleteView(SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy('facebook:post-campaign.index')
    queryset = models.FacebookPostCampaign.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar campaña: ",
        "modal_title": "Eliminar campaña: ",
        "modal_description": "Eliminar campaña",
        "cancel_url": success_url
    }
    success_message = "Campaña {name} eliminada exitosamente"


class FacebookPostCampaignToggleStatusView(SuccessMessageMixin, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:post-campaign.index')
    queryset = models.FacebookPostCampaign.objects.all()
    success_message = "Campaña {name} activado/desactivado exitosamente"


class FacebookPostCampaignDuplicateView(DuplicateView):
    success_url = reverse_lazy('facebook:post-campaign.index')
    success_message = "Campaña duplicada correctamente correctamente"
    queryset = models.FacebookPostCampaign.objects.all()
    template_name = 'facebook/post_campaings/duplicate.html'


class PublishNowFacebookPostCampaignView(SuccessMessageMixin, FilterView, FormView):
    filterset_class = filters.FacebookPostCampaingFilterSet
    form_class = forms.PublishFacebookPostCampaignForm
    queryset = models.FacebookPostCampaign.objects.filter(active=True).all()
    template_name = 'facebook/post_campaings/publish_now.html'
    success_message = "Estados enviados a publicar correctamente"
    success_url = reverse_lazy('facebook:post-campaign.index')

    def form_valid(self, form):
        form.publish()
        return super().form_valid(form)
