from data_fetcher.global_request_context import get_request
from django import forms

from core.forms import PublishNowForm
from core.forms.widgets import DatePickerInput
from facebook import models
from facebook.tasks import enqueue_facebook_campaign


class CurrentUserProfile(forms.ModelForm):
    profile = forms.ModelChoiceField(queryset=models.FacebookProfile.objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile'].queryset = models.FacebookProfile.user_objects.all()


class FacebookAccountForm(forms.ModelForm):
    class Meta:
        model = models.FacebookProfile
        exclude = ['context', 'created_by']


class FacebookAgentForm(CurrentUserProfile):
    class Meta:
        model = models.FacebookAgent
        exclude = ['leads_found', 'limit']


class FacebookDistributionListCreateForm(CurrentUserProfile):
    class Meta:
        model = models.FacebookDistributionList
        exclude = ['groups', 'active']


class FacebookDistributionListUpdateForm(CurrentUserProfile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile'].disabled = True
        self.fields['groups'].queryset = models.FacebookGroup.objects.filter(profile=kwargs['instance'].profile)

    class Meta:
        model = models.FacebookDistributionList
        fields = forms.ALL_FIELDS


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


class PublishFacebookPostCampaignForm(PublishNowForm):
    items = forms.ModelMultipleChoiceField(queryset=models.FacebookPostCampaign.objects.all())

    def publish(self):
        enqueue_facebook_campaign(self.cleaned_data['items'])
