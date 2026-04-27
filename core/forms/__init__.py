from django import forms


class PublishNowForm(forms.Form):
    items = forms.ModelMultipleChoiceField(queryset=None)
