from django import forms

from facebook import models


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
        exclude = ['contacts', 'groups', 'active']


class FacebookDistributionListUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FacebookDistributionListUpdateForm, self).__init__(*args, **kwargs)
        self.fields['account'].disabled = True
        self.fields['contacts'].queryset = models.FacebookGroup.objects.filter(profile=kwargs['instance'].profile)

    class Meta:
        model = models.FacebookGroupCategory
        fields = forms.ALL_FIELDS
