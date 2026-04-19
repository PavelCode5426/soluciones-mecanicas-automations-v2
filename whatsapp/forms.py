from urllib.request import urlopen

from dateutil.utils import today
from django import forms
from django.core.cache import cache
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from rest_framework.reverse import reverse

from core.forms.widgets import DatePickerInput, TimePickerInput
from whatsapp.factories import create_whatsapp_service
from whatsapp.models import WhatsAppStatus, WhatsAppContact, WhatsAppAccount, WhatsAppDistributionList, WhatsAppGroup, \
    WhatsAppMessage
from whatsapp.tasks import syncronize_whatsapp_account_groups

ACTIVE_FIELD = forms.ChoiceField(choices=[(True, 'Activo'), (False, 'Inactivo')], widget=forms.Select)


class RemoveActiveOnCreateMixin(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not kwargs.get('instance'):
            self.fields.pop('active')


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


class WhatsAppMessageForm(forms.ModelForm):
    from_date = forms.DateField(widget=DatePickerInput, initial=today)

    class Meta:
        model = WhatsAppMessage
        exclude = ['published_count']
        widgets = {
            'from_date': DatePickerInput(),
            'until_date': DatePickerInput(),
        }


class WhatsAppContactForm(RemoveActiveOnCreateMixin, forms.ModelForm):
    push_name = forms.CharField(disabled=True)
    chat_id = forms.CharField(disabled=True)

    class Meta:
        model = WhatsAppContact
        fields = ['name', 'push_name', 'chat_id', 'active']


class WhatsAppCreateAccountForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(WhatsAppCreateAccountForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(WhatsAppCreateAccountForm, self).save(commit=commit)
        self.synchronise_account(instance)
        return instance

    def synchronise_account(self, obj):
        service = create_whatsapp_service(obj)
        # is_new_account = obj.pk is None
        # if is_new_account:
        #     service.create_session()

        obj.save()
        profile = service.get_profile_info()
        obj.name = profile['name']
        obj.chat_id = profile['id']

        img_temp = NamedTemporaryFile()
        with urlopen(profile['picture']) as response:
            img_temp.write(response.read())
            img_temp.flush()
            obj.avatar.save(f"{obj.name}.jpg", File(img_temp), save=False)

        obj.save()
        cache.delete(obj.session)

        syncronize_whatsapp_account_groups(obj)
        # syncronize_whatsapp_account_contacts(obj)
        webhooks_urls = []
        if obj.can_auto_reply:
            webhooks_urls.append(self.request.build_absolute_uri(reverse('whatsapp:chats-webhook')))
        if obj.can_find_leads:
            webhooks_urls.append(self.request.build_absolute_uri(reverse('whatsapp:groups-webhook')))
        service.update_session(webhooks_urls)

    class Meta:
        model = WhatsAppAccount
        fields = ['session']


class WhatsAppUpdateAccountForm(WhatsAppCreateAccountForm):
    class Meta:
        model = WhatsAppAccount
        fields = forms.ALL_FIELDS


class WhatsAppDistributionListCreateForm(forms.ModelForm):
    class Meta:
        model = WhatsAppDistributionList
        exclude = ['contacts', 'groups', 'active']


class WhatsAppDistributionListUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(WhatsAppDistributionListUpdateForm, self).__init__(*args, **kwargs)
        self.fields['account'].disabled = True
        self.fields['contacts'].queryset = WhatsAppContact.objects.filter(account=kwargs['instance'].account)
        self.fields['groups'].queryset = WhatsAppGroup.objects.filter(account=kwargs['instance'].account)

    class Meta:
        model = WhatsAppDistributionList
        fields = forms.ALL_FIELDS
