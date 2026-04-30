from django import forms

from core.forms import PublishNowForm
from core.forms.widgets import DatePickerInput
from facebook import models
from facebook.tasks import enqueue_facebook_campaign


class CurrentUserProfile(forms.ModelForm):
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
        exclude = ['leads_found']


class FacebookDistributionListCreateForm(CurrentUserProfile):
    class Meta:
        model = models.FacebookDistributionList
        exclude = ['groups', 'active']


class FacebookDistributionListUpdateForm(CurrentUserProfile):
    def __init__(self, *args, **kwargs):
        super(CurrentUserProfile, self).__init__(*args, **kwargs)
        self.fields['profile'].disabled = True
        self.fields['groups'].queryset = models.FacebookGroup.objects.filter(profile=kwargs['instance'].profile)

    class Meta:
        model = models.FacebookDistributionList
        fields = forms.ALL_FIELDS


class FacebookPostCampaignForm(CurrentUserProfile):
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
        for items in self.cleaned_data['items']:
            enqueue_facebook_campaign(items)
