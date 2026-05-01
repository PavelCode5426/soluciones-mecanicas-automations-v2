from django import forms


class PublishNowForm(forms.Form):
    items = forms.ModelMultipleChoiceField(queryset=None)

    def clean_items(self):
        items = self.cleaned_data['items']
        if not isinstance(items, list):
            items = [items]
        return items
