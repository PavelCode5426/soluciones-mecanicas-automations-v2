from django.db.models import Q
from django.utils.timezone import now
from django_q.tasks import async_task

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
                       .all())

    for status in whatsapp_status:
        async_task(
            publish_whatsapp_status, status,
            task_name=f'create_whatsapp_status_{status.pk}',
            group='whatsapp_status',
            cluster='high_priority',
        )
    return f"Programados {whatsapp_status.count()} estados de whatsapp"


def enqueue_active_messages():
    messages = (WhatsAppMessage.objects.select_related('account')
                .filter(active=True, from_date__lte=now())
                .filter(Q(until_date__gte=now()) | Q(until_date__isnull=True))
                .all())

    for message in messages:
        enqueue_whatsapp_message(message, refresh=False)
    return f"Programados {len(messages)} mensajes de whatsapp"