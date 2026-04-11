import datetime
from datetime import datetime

from dateutil.utils import today
from django.db.models import Q
from django.utils.timezone import now
from django_q.models import Schedule, Task
from django_q.tasks import async_task, schedule

from whatsapp.models import WhatsAppStatus, WhatsAppAccount, WhatsAppMessage
from whatsapp.tasks import publish_whatsapp_status, syncronize_whatsapp_account_groups, \
    syncronize_whatsapp_account_contacts, enqueue_whatsapp_message


def update_whatsapp_contacts_and_groups():
    accounts = WhatsAppAccount.objects.all()

    for account in accounts:
        syncronize_whatsapp_account_groups(account)
        syncronize_whatsapp_account_contacts(account)


def enqueue_active_status():
    whatsapp_status = (WhatsAppStatus.objects.select_related('account')
                       .filter(active=True, from_date__lte=now())
                       .filter(Q(until_date__gte=now()) | Q(until_date__isnull=True))
                       .filter(publish_at__hour=now().hour, weekdays__day=now().weekday())
                       .all())

    for status in whatsapp_status:
        async_task(
            publish_whatsapp_status, status,
            name=f'create_whatsapp_status_{status.pk}',
            cluster='whatsapp',
            next_run=datetime.combine(now(), status.publish_at)
        )

    return f"Programados {whatsapp_status.count()} estados de whatsapp"


def enqueue_active_messages():
    messages = (WhatsAppMessage.objects.select_related('account')
                .filter(active=True, from_date__lte=now())
                .filter(Q(until_date__gte=now()) | Q(until_date__isnull=True))
                .filter(publish_at__hour=now().hour, weekdays__day=now().weekday())
                .all())

    for message in messages:
        enqueue_whatsapp_message(message, refresh=False)
    return f"Programados {len(messages)} mensajes de whatsapp"
