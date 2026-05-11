from data_fetcher.global_request_context import get_request
from django import forms

from core.forms import PublishNowForm
from core.forms.widgets import DatePickerInput
from facebook import models
from facebook.tasks import enqueue_facebook_campaign


class FacebookFileForm(forms.ModelForm):
    class Meta:
        model = models.FacebookFile
        fields = ['file']


# FacebookFileInlineFormSet = inlineformset_factory(
#     models.FacebookPostCampaign, models.FacebookFile,
#     fields=['file'], extra=5, absolute_max=5, can_delete=True)


class CurrentUserProfile(forms.ModelForm):
    profile = forms.ModelChoiceField(queryset=models.FacebookProfile.objects.none(), required=True, label="Cuenta")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile'].queryset = models.FacebookProfile.user_objects.all()


class FacebookAccountForm(forms.ModelForm):
    class Meta:
        model = models.FacebookProfile
        exclude = ['context', 'created_by', 'real_accounts']
        labels = {
            'name': 'Nombre de la cuenta', 'can_find_leads': 'Puede buscar clientes automáticamente',
            'active': 'Activo', 'can_post_in_groups': 'Puede publicar en grupos',
            'posts_footer': 'Pie de publicación'
        }


class FacebookAgentForm(CurrentUserProfile):
    class Meta:
        model = models.FacebookAgent
        exclude = ['leads_found', 'limit']
        labels = {
            'name': 'Nombre del agente', 'distribution_list': 'Lista de distribuciones de la cuenta',
            'agent_description': 'Descripción del agente', 'search_keyword': 'Críterio de búsqueda',
            'classificator_prompt': 'Instrucciones de clasificación',
            'agent_prompt': 'Instrucciones del agente', 'active': 'Activo'
        }


class FacebookDistributionListCreateForm(CurrentUserProfile):
    class Meta:
        model = models.FacebookDistributionList
        exclude = ['groups', 'active']
        labels = {
            'name': 'Nombre de la lista',
        }


class FacebookDistributionListUpdateForm(CurrentUserProfile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile'].disabled = True
        self.fields['groups'].queryset = models.FacebookGroup.objects.filter(
            profiles__profile=kwargs['instance'].profile)

    class Meta:
        model = models.FacebookDistributionList
        fields = forms.ALL_FIELDS
        labels = {
            'name': 'Nombre de la lista', 'groups': 'Grupos de la cuenta',
        }


class FacebookPostCampaignForm(CurrentUserProfile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['distribution_lists'].queryset = models.FacebookDistributionList.objects \
            .filter(profile__created_by=get_request().user).all()

    class Meta:
        model = models.FacebookPostCampaign
        exclude = ['published_count', 'distribution_count']
        widgets = {
            'from_date': DatePickerInput(),
            'until_date': DatePickerInput(),
        }
        labels = {
            'name': 'Nombre de la campaña',
            'text': "Contenido de la publicación", 'title': 'Título de la publicación',
            'active': 'Activo', 'file': 'Archivo', 'from_date': 'Desde',
            'until_date': 'Hasta', 'distribution_lists': 'Listas de distribución',
            'schedules': 'Horarios'
        }


class PublishFacebookPostCampaignForm(PublishNowForm):
    items = forms.ModelMultipleChoiceField(queryset=models.FacebookPostCampaign.objects.all())

    def publish(self):
        enqueue_facebook_campaign(self.cleaned_data['items'])
