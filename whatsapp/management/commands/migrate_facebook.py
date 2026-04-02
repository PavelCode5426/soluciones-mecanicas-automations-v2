from django.core.management.base import BaseCommand

from facebook.models import FacebookPostCampaign
from whatsapp.helpers import get_message_type
from whatsapp.models import WhatsAppStatus, WhatsAppAccount, WhatsAppMessage


class Command(BaseCommand):
    help = "Sincroniza la informacion de facebook con los mensajes de whatsapp"

    def handle(self, *args, **options):
        facebook_post = FacebookPostCampaign.objects.all()
        account = WhatsAppAccount.objects.first()

        for post in facebook_post:
            message_type = get_message_type(post.file)
            WhatsAppStatus.objects.update_or_create(
                defaults={"caption": post.text, "file": post.file},
                create_defaults={
                    "name": post.name,
                    "caption": post.text,
                    "file": post.file,
                },
                account=account,
                name=post.name,
            )

            WhatsAppMessage.objects.update_or_create(
                defaults={
                    "message": post.text, "file": post.file,
                    "frequency": post.frequency,
                    "message_type": message_type

                },
                create_defaults={
                    "name": post.name,
                    "message": post.text,
                    "file": post.file,
                    "frequency": post.frequency,
                    "message_type": message_type
                },
                account=account,
                name=post.name,
            )
