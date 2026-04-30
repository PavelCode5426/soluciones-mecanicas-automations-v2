from django.db.models import Q, F, ExpressionWrapper, DecimalField
from django.utils.timezone import localtime

from whatsapp.models import WhatsAppStatus, WhatsAppAccount, WhatsAppMessage
from whatsapp.tasks import syncronize_whatsapp_account_groups, \
    syncronize_whatsapp_account_contacts, enqueue_whatsapp_message, enqueue_whatsapp_status


def update_whatsapp_contacts_and_groups():
    accounts = WhatsAppAccount.all_objects.all()

    for account in accounts:
        syncronize_whatsapp_account_groups(account)
        syncronize_whatsapp_account_contacts(account)


def enqueue_active_status():
    current_time = localtime()
    current_weekday = current_time.weekday()

    # whatsapp_status = (WhatsAppStatus.all_objects.select_related('account')
    #                    .filter(active=True, account__active=True, from_date__lte=localtime())
    #                    .filter(Q(until_date__gte=localtime()) | Q(until_date__isnull=True))
    #                    # .filter(publish_at=localtime(), weekdays__day=localtime().weekday())
    #                    .filter(weekdays__day=localtime().weekday())
    #                    .all())

    whatsapp_status = WhatsAppStatus.objects.select_related('account') \
        .filter(active=True, account__active=True, from_date__lte=current_time) \
        .filter(Q(until_date__gte=current_time) | Q(until_date__isnull=True)) \
        .filter(weekdays__day=current_weekday, schedule__time=current_time) \
        .order_by('account', 'order').all()

    for status in whatsapp_status:
        enqueue_whatsapp_status(status)

    return f"Programados {whatsapp_status.count()} estados de whatsapp"


def enqueue_active_messages():
    current_time = localtime()
    current_hour = current_time.hour
    current_weekday = current_time.weekday()

    messages = WhatsAppMessage.objects.select_related('account') \
        .exclude(frequency__isnull=True) \
        .filter(active=True, account__active=True, from_date__lte=current_time) \
        .filter(Q(until_date__gte=current_time) | Q(until_date__isnull=True)) \
        .filter(from_time__lte=current_time, until_time__gte=current_time) \
        .filter(weekdays__day=current_weekday) \
        .annotate(can_publish=ExpressionWrapper(current_hour % F('frequency'), DecimalField())) \
        .filter(can_publish=0)

    next_version_messages = WhatsAppMessage.objects.select_related('account') \
        .filter(active=True, account__active=True, from_date__lte=current_time) \
        .filter(Q(until_date__gte=current_time) | Q(until_date__isnull=True)) \
        .filter(weekdays__day=current_weekday) \
        .filter(schedules__schedule__time=current_time) \
        .order_by('account', 'schedules__order').all()

    # TODO REGRESAR ESTO ATRAS
    # messages.update(last_whatsapp_id=None)
    for message in messages.all():
        enqueue_whatsapp_message(message, refresh=False)
    return f"Programados {len(next_version_messages)} mensajes de whatsapp a las {localtime()}"
