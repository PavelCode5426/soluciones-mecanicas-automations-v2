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
