from django import forms

from facebook import models


class FacebookUpdateAccountForm(forms.ModelForm):
    class Meta:
        model = models.FacebookProfile
        exclude = ['context']
