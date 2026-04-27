from django import forms

from core.forms import PublishNowForm
from core.forms.widgets import DatePickerInput
from facebook import models
from facebook.tasks import enqueue_facebook_campaign


class FacebookAccountForm(forms.ModelForm):
    class Meta:
        model = models.FacebookProfile
        exclude = ['context']


class FacebookAgentForm(forms.ModelForm):
    class Meta:
        model = models.FacebookLeadExplorer
        exclude = ['leads_found']


class FacebookDistributionListCreateForm(forms.ModelForm):
    class Meta:
        model = models.FacebookGroupCategory
        exclude = ['groups', 'active']


class FacebookDistributionListUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FacebookDistributionListUpdateForm, self).__init__(*args, **kwargs)
        self.fields['profile'].disabled = True
        self.fields['groups'].queryset = models.FacebookGroup.objects.filter(profile=kwargs['instance'].profile)

    class Meta:
        model = models.FacebookGroupCategory
        fields = forms.ALL_FIELDS


class FacebookPostCampaignForm(forms.ModelForm):
    class Meta:
        model = models.FacebookPostCampaign
        exclude = ['published_count','distribution_count']
        widgets = {
            'from_date': DatePickerInput(),
            'until_date': DatePickerInput(),
        }


class PublishFacebookPostCampaignForm(PublishNowForm):
    items = forms.ModelMultipleChoiceField(queryset=models.FacebookPostCampaign.objects.all())

    def publish(self):
        for items in self.cleaned_data['items']:
            enqueue_facebook_campaign(items)
