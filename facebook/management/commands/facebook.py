from django.core.management.base import BaseCommand

from facebook.models import FacebookProfile
from facebook.tasks import download_groups_task


class Command(BaseCommand):
    help = "Sincroniza la informacion de facebook con la base de datos"

    def handle(self, *args, **options):
        user = FacebookProfile.objects.first()
        download_groups_task(user)
