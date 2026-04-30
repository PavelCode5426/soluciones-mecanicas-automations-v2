from urllib.request import urlopen

from data_fetcher.global_request_context import get_request
from dateutil.utils import today
from django import forms
from django.core.cache import cache
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db.models import Max
from django.forms import modelformset_factory
from rest_framework.reverse import reverse

from core.forms import PublishNowForm
from core.forms.widgets import DatePickerInput
from core.models import Schedule
from whatsapp.factories import create_whatsapp_service
from whatsapp.helpers import get_message_type
from whatsapp.models import WhatsAppStatus, WhatsAppContact, WhatsAppAccount, WhatsAppDistributionList, WhatsAppGroup, \
    WhatsAppMessage, WhatsAppScheduleMessage
from whatsapp.tasks import syncronize_whatsapp_account_groups, enqueue_whatsapp_status, enqueue_whatsapp_message

ACTIVE_FIELD = forms.ChoiceField(choices=[(True, 'Activo'), (False, 'Inactivo')], widget=forms.Select)


class CurrentUserAccount:
    account = forms.ModelChoiceField(queryset=WhatsAppAccount.objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = WhatsAppAccount.user_objects.all()


class RemoveActiveOnCreateMixin(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not kwargs.get('instance'):
            self.fields.pop('active')


class WhatsAppStatusAdminForm(forms.ModelForm):
    sync_schedule = forms.BooleanField(initial=False, required=False)

    def save(self, commit=True):
        instance = super(WhatsAppStatusAdminForm, self).save(commit=commit)
        if self.cleaned_data['sync_schedule']:
            weekdays = instance.weekdays.all()
            WhatsAppStatus.objects.filter(active=True, account=instance.account).update(
                from_date=instance.from_date,
                until_date=instance.until_date,
                publish_at=instance.publish_at,
            )
            status = WhatsAppStatus.objects.filter(active=True, account=instance.account).exclude(pk=instance.pk).all()
            for _status in status:
                _status.weekdays.set(weekdays)

        return instance

    class Meta:
        model = WhatsAppStatus
        fields = forms.ALL_FIELDS


class WhatsAppMessageAdminForm(forms.ModelForm):
    sync_schedule = forms.BooleanField(initial=False, required=False)

    def save(self, commit=True):
        instance = super(WhatsAppMessageAdminForm, self).save(commit=commit)
        if self.cleaned_data['sync_schedule']:
            weekdays = instance.weekdays.all()
            WhatsAppMessage.objects.filter(active=True, account=instance.account).update(
                frequency=instance.frequency,
                from_date=instance.from_date,
                until_date=instance.until_date,
                from_time=instance.from_time,
                until_time=instance.until_time,
            )
            messages = WhatsAppMessage.objects.filter(active=True, account=instance.account).exclude(
                pk=instance.pk).all()
            for _message in messages:
                _message.weekdays.set(weekdays)

        return instance

    class Meta:
        model = WhatsAppMessage
        fields = forms.ALL_FIELDS


class WhatsAppStatusForm(CurrentUserAccount, forms.ModelForm):
    from_date = forms.DateField(widget=DatePickerInput, initial=today)

    class Meta:
        model = WhatsAppStatus
        exclude = ['published_count', 'order']
        widgets = {
            'from_date': DatePickerInput(),
            'until_date': DatePickerInput(),
        }


class WhatsAppMessageForm(CurrentUserAccount, forms.ModelForm):
    schedules = forms.ModelMultipleChoiceField(Schedule.objects.all())

    def save(self, commit=True):
        instance = super().save(commit=commit)
        instance.message_type = 'text' if not instance.file else get_message_type(instance.file)
        if commit:
            instance.save()
        return instance

    def _save_m2m(self):
        super(WhatsAppMessageForm, self)._save_m2m()
        schedules = self.cleaned_data['schedules']
        WhatsAppScheduleMessage.objects.filter(message=self.instance).exclude(schedule__in=schedules).delete()
        for schedule in schedules:
            last_order = WhatsAppScheduleMessage.objects \
                             .filter(schedule=schedule, message__account=self.instance.account) \
                             .aggregate(Max("order"))["order__max"] or 0

            WhatsAppScheduleMessage.objects.get_or_create(
                defaults={'message': self.instance, 'schedule': schedule, 'order': last_order + 1},
                message=self.instance, schedule=schedule)

    class Meta:
        model = WhatsAppMessage
        exclude = ['published_count', 'order', ]
        widgets = {
            'from_date': DatePickerInput(),
            'until_date': DatePickerInput(),
        }


class WhatsAppContactForm(RemoveActiveOnCreateMixin, forms.ModelForm):
    push_name = forms.CharField(disabled=True,required=False)
    chat_id = forms.CharField(disabled=True)

    class Meta:
        model = WhatsAppContact
        fields = ['name', 'push_name', 'chat_id', 'active']


class WhatsAppCreateAccountForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = get_request()
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
    chat_id = forms.CharField(disabled=True)
    session = forms.CharField(disabled=True)

    class Meta:
        model = WhatsAppAccount
        exclude = ['created_by']


class WhatsAppDistributionListCreateForm(CurrentUserAccount, forms.ModelForm):
    class Meta:
        model = WhatsAppDistributionList
        exclude = ['contacts', 'groups', 'active']


class WhatsAppDistributionListUpdateForm(CurrentUserAccount, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(WhatsAppDistributionListUpdateForm, self).__init__(*args, **kwargs)
        self.fields['account'].disabled = True
        self.fields['contacts'].queryset = WhatsAppContact.objects.filter(account=kwargs['instance'].account)
        self.fields['groups'].queryset = WhatsAppGroup.objects.filter(account=kwargs['instance'].account)

    class Meta:
        model = WhatsAppDistributionList
        fields = forms.ALL_FIELDS


WhatAppSortMessageFormSet = modelformset_factory(
    WhatsAppScheduleMessage,
    fields=['order'],
    widgets={'order': forms.HiddenInput()},
    extra=0,
    can_order=True,
)

WhatAppSortStatusFormSet = modelformset_factory(
    WhatsAppStatus,
    fields=['order'],
    widgets={'order': forms.HiddenInput()},
    extra=0,
    can_order=True,
)


class PublishWhastAppStatusForm(PublishNowForm):
    items = forms.ModelMultipleChoiceField(queryset=WhatsAppStatus.objects.all())

    def publish(self):
        for status in self.cleaned_data['items']:
            enqueue_whatsapp_status(status)


class PublishWhastAppMessagesForm(PublishNowForm):
    items = forms.ModelMultipleChoiceField(queryset=WhatsAppMessage.objects.all())

    def publish(self):
        for message in self.cleaned_data['items']:
            enqueue_whatsapp_message(message)
