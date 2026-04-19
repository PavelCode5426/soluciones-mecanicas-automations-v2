from dateutil.utils import today
from django import forms

from core.forms.widgets import DatePickerInput, TimePickerInput
from whatsapp.models import WhatsAppStatus, WhatsAppContact


class WhatsAppStatusAdminForm(forms.ModelForm):
    sync_schedule = forms.BooleanField(initial=False, required=False)

    def save(self, commit=True):
        instance = super(WhatsAppStatusAdminForm, self).save(commit=False)
        if self.cleaned_data['sync_schedule']:
            weekdays = instance.weekdays.all()
            WhatsAppStatus.objects.filter(active=True, account=instance.account).update(
                from_date=instance.from_date,
                until_date=instance.until_date,
                publish_at=instance.publish_at,
                published_count=instance.published_count
            )
            status = WhatsAppStatus.objects.filter(active=True, account=instance.account).exclude(pk=instance.pk).all()
            for _status in status:
                _status.weekdays.set(weekdays)

        return instance

    class Meta:
        model = WhatsAppStatus
        fields = forms.ALL_FIELDS


class WhatsAppStatusForm(forms.ModelForm):
    from_date = forms.DateField(widget=DatePickerInput, initial=today)

    class Meta:
        model = WhatsAppStatus
        exclude = ['published_count']
        widgets = {
            'from_date': DatePickerInput(),
            'until_date': DatePickerInput(),
            'publish_at': TimePickerInput(),
        }


class WhatsAppContactForm(forms.ModelForm):
    push_name = forms.CharField(disabled=True)
    chat_id = forms.CharField(disabled=True)

    class Meta:
        model = WhatsAppContact
        fields = ['name', 'push_name', 'chat_id', 'active']
