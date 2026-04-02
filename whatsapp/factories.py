from django.conf import settings

from services.whatsapp import WAHAService
from whatsapp.models import WhatsAppAccount

__waha_services = dict()


def create_whatsapp_service(account: WhatsAppAccount):
    instance = __waha_services.get(account.session)
    if not instance:
        instance = WAHAService(
            settings.WAHA_SERVER_URL,
            account.session,
            settings.WAHA_APIKEY,
            settings.WAHA_USERNAME,
            settings.WAHA_PASSWORD,
        )

        __waha_services.setdefault(account.session, instance)

    return instance
