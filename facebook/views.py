from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django_filters.views import FilterView

from core.generics import ToggleStatusView, DuplicateView
from facebook import forms, filters
from facebook import models
from facebook.mixins import FacebookProfileViewMixins, FilterByProfileViewMixins


class FacebookAccountsListView(FacebookProfileViewMixins, ListView):
    template_name = 'facebook/accounts/index.html'


class FacebookAccountDetailView(FacebookProfileViewMixins, DetailView):
    template_name = 'whatsapp/accounts/details.html'


class FacebookAccountsCreateView(SuccessMessageMixin, CreateView):
    success_url = reverse_lazy('facebook:accounts.index')
    form_class = forms.FacebookAccountForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nueva cuenta",
        "cancel_url": success_url
    }
    success_message = "Cuenta %(name)s creada exitosamente"


class FacebookAccountsUpdateView(SuccessMessageMixin, FacebookProfileViewMixins, UpdateView):
    success_url = reverse_lazy('facebook:accounts.index')
    form_class = forms.FacebookAccountForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Actualizar cuenta: ",
        "cancel_url": success_url
    }
    success_message = "Cuenta %(name)s actualizada exitosamente"


class FacebookAccountsToggleStatusView(SuccessMessageMixin, FacebookProfileViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:accounts.index')

    def get_success_message(self, cleaned_data):
        return f"Cuenta {self.object} activada/desactivada  exitosamente"


class FacebookAccountsDeleteView(SuccessMessageMixin, FacebookProfileViewMixins, DeleteView):
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


class FacebookGroupsListView(FilterByProfileViewMixins, FilterView):
    template_name = 'facebook/groups/index.html'
    filterset_class = filters.FacebookGroupsFilterSet
    queryset = models.FacebookProfileGroup.objects.all()
    paginate_by = 100


class FacebookGroupsToggleStatusView(SuccessMessageMixin, FilterByProfileViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:groups.index')
    queryset = models.FacebookProfileGroup.objects.all()
    success_message = "Grupo activado/desactivado exitosamente"


class FacebookAgentListView(FilterByProfileViewMixins, ListView):
    template_name = 'facebook/agents/index.html'
    queryset = models.FacebookAgent.objects.all()


# TODO TERMINAR ESTA VISTA
class FacebookAgentDetailView(FilterByProfileViewMixins, DetailView):
    template_name = 'whatsapp/accounts/details.html'


class FacebookAgentCreateView(SuccessMessageMixin, CreateView):
    success_url = reverse_lazy('facebook:agents.index')
    form_class = forms.FacebookAgentForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nuevo agente",
        "cancel_url": success_url
    }
    success_message = "Agente %(name)s creado exitosamente"


class FacebookAgentUpdateView(SuccessMessageMixin, FilterByProfileViewMixins, UpdateView):
    success_url = reverse_lazy('facebook:agents.index')
    form_class = forms.FacebookAgentForm
    queryset = models.FacebookAgent.objects.all()
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Actualizar agente: ",
        "cancel_url": success_url
    }
    success_message = "Agente %(name)s actualizado exitosamente"


class FacebookAgentToggleStatusView(SuccessMessageMixin, FilterByProfileViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:agents.index')
    queryset = models.FacebookAgent.objects.all()

    def get_success_message(self, cleaned_data):
        return f"Agente {self.object} activado/desactivado exitosamente"


class FacebookDistributionListsListView(FilterByProfileViewMixins, ListView):
    template_name = 'facebook/distribucion_lists/index.html'
    queryset = models.FacebookDistributionList.objects.all()


class FacebookDistributionListsCreateView(SuccessMessageMixin, FilterByProfileViewMixins, CreateView):
    # success_url = reverse_lazy('whatsapp:distribution-lists.update')
    form_class = forms.FacebookDistributionListCreateForm
    template_name = 'layout/admin_form_layout.html'
    extra_context = {
        "page_title": "Crear nueva lista de distribución",
        "cancel_url": reverse_lazy('whatsapp:distribution-lists.index')
    }
    success_message = "Lista de distribución %(name)s creada exitosamente"

    def get_success_url(self):
        return str(reverse_lazy('facebook:distribution-lists.update', kwargs=dict(pk=self.object.pk)))


class FacebookDistributionListsUpdateView(SuccessMessageMixin, FilterByProfileViewMixins, UpdateView):
    success_url = reverse_lazy('facebook:distribution-lists.index')
    form_class = forms.FacebookDistributionListUpdateForm
    queryset = models.FacebookDistributionList.objects.all()
    template_name = 'facebook/distribucion_lists/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar lista de distribución: ",
        "cancel_url": success_url
    }
    success_message = "Lista de distribución %(name)s actualizada exitosamente"


class FacebookDistributionListsToggleStatusView(SuccessMessageMixin, FilterByProfileViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:distribution-lists.index')
    queryset = models.FacebookDistributionList.objects.all()

    def get_success_message(self, cleaned_data):
        return f"Lista de distribución {self.object} activado/desactivado exitosamente"


class FacebookDistributionListsDeleteView(SuccessMessageMixin, FilterByProfileViewMixins, DeleteView):
    success_url = reverse_lazy('facebook:distribution-lists.index')
    queryset = models.FacebookDistributionList.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar lista de distribución: ",
        "modal_title": "Eliminar lista de distribución: ",
        "modal_description": "Eliminar lista de distribución",
        "cancel_url": success_url
    }

    def get_success_message(self, cleaned_data):
        return f"Lista de distribución {self.object} eliminada exitosamente"


class FacebookPostCampaignListView(FilterByProfileViewMixins, FilterView):
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
    success_message = "Nueva campaña %(name)s creada exitosamente"

    # def form_valid(self, form):
    #     return super(SuccessMessageMixin).form_valid(form)
    #
    # def post(self, request, *args, **kwargs):
    #     form = self.get_form()
    #     formset = forms.FacebookFileInlineFormSet(request.POST, request.FILES)
    #     if form.is_valid() and formset.is_valid():
    #         post = form.save()
    #         instances = formset.save(commit=False)
    #         for instance in instances:
    #             instance.content_object = post
    #             instance.save()
    #         return self.form_invalid(form)
    #     else:
    #         return self.form_invalid(form)


class FacebookPostCampaignUpdateView(SuccessMessageMixin, FilterByProfileViewMixins, UpdateView):
    success_url = reverse_lazy('facebook:post-campaign.index')
    form_class = forms.FacebookPostCampaignForm
    queryset = models.FacebookPostCampaign.objects.all()
    template_name = 'facebook/post_campaings/create_or_update.html'
    extra_context = {
        "page_title": "Actualizar campaña: ",
        "cancel_url": success_url
    }
    success_message = "Campaña %(name)s actualizada exitosamente"


class FacebookPostCampaignDeleteView(SuccessMessageMixin, FilterByProfileViewMixins, DeleteView):
    success_url = reverse_lazy('facebook:post-campaign.index')
    queryset = models.FacebookPostCampaign.objects.all()
    template_name = 'layout/admin_delete_layout.html'
    extra_context = {
        "page_title": "Eliminar campaña: ",
        "modal_title": "Eliminar campaña: ",
        "modal_description": "Eliminar campaña",
        "cancel_url": success_url
    }

    def get_success_message(self, cleaned_data):
        return f"Campaña {self.object} eliminada exitosamente"


class FacebookPostCampaignToggleStatusView(SuccessMessageMixin, FilterByProfileViewMixins, ToggleStatusView):
    http_method_names = ['post']
    success_url = reverse_lazy('facebook:post-campaign.index')
    queryset = models.FacebookPostCampaign.objects.all()

    def get_success_message(self, cleaned_data):
        return f"Campaña {self.object} activado/desactivado exitosamente"


class FacebookPostCampaignDuplicateView(FilterByProfileViewMixins, DuplicateView):
    success_url = reverse_lazy('facebook:post-campaign.index')
    queryset = models.FacebookPostCampaign.objects.all()
    template_name = 'facebook/post_campaings/duplicate.html'

    def duplicate_object(self):
        old_object = self.get_object()
        super().duplicate_object()
        self.object.distribution_lists.set(old_object.distribution_lists.all())
        self.object.schedules.set(old_object.schedules.all())
        self.object.save()

    def get_success_message(self, cleaned_data):
        return f"Campaña {self.object} duplicada exitosamente"


class PublishNowFacebookPostCampaignView(SuccessMessageMixin, FilterByProfileViewMixins, FilterView, FormView):
    filterset_class = filters.FacebookPostCampaingFilterSet
    form_class = forms.PublishFacebookPostCampaignForm
    queryset = models.FacebookPostCampaign.objects.filter(active=True).all()
    template_name = 'facebook/post_campaings/publish_now.html'
    success_message = "Campañas enviadas a publicar correctamente"
    success_url = reverse_lazy('facebook:post-campaign.index')

    def form_valid(self, form):
        form.publish()
        return super().form_valid(form)
