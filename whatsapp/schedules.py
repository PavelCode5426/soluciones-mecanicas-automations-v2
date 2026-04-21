from django.db.models import Q, F, ExpressionWrapper, DecimalField
from django.utils.timezone import localtime
from django_q.tasks import async_task

from whatsapp.models import WhatsAppStatus, WhatsAppAccount, WhatsAppMessage
from whatsapp.tasks import publish_whatsapp_status, syncronize_whatsapp_account_groups, \
    syncronize_whatsapp_account_contacts, enqueue_whatsapp_message, enqueue_whatsapp_status


def update_whatsapp_contacts_and_groups():
    accounts = WhatsAppAccount.objects.all()

    for account in accounts:
        syncronize_whatsapp_account_groups(account)
        syncronize_whatsapp_account_contacts(account)


def enqueue_active_status():
    whatsapp_status = (WhatsAppStatus.objects.select_related('account')
                       .filter(active=True, from_date__lte=localtime())
                       .filter(Q(until_date__gte=localtime()) | Q(until_date__isnull=True))
                       # .filter(publish_at=localtime(), weekdays__day=localtime().weekday())
                       .filter(weekdays__day=localtime().weekday())
                       .all())

    for status in whatsapp_status:
        enqueue_whatsapp_status(status)

    return f"Programados {whatsapp_status.count()} estados de whatsapp"


def enqueue_active_messages():
    current_time = localtime()
    current_hour = current_time.hour
    current_weekday = current_time.weekday()

    messages = (WhatsAppMessage.objects.select_related('account')
                .exclude(frequency__isnull=True, account__active=False)
                .filter(active=True, from_date__lte=current_time)
                .filter(Q(until_date__gte=current_time) | Q(until_date__isnull=True))
                .filter(from_time__lte=current_time, until_time__gte=current_time)
                .filter(weekdays__day=current_weekday)
                .annotate(can_publish=ExpressionWrapper(current_hour % F('frequency'), DecimalField()))
                .filter(can_publish=0)
                .all())

    for message in messages:
        enqueue_whatsapp_message(message, refresh=False)
    return f"Programados {len(messages)} mensajes de whatsapp a las {localtime()}"
