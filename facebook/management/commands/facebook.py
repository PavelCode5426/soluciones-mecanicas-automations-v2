import os
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from facebook.models import FacebookGroup, FacebookProfile
from facebook.tasks import download_groups_task


class Command(BaseCommand):
    help = "Sincroniza la informacion de facebook con la base de datos"

    def handle(self, *args, **options):
        for profile in FacebookProfile.objects.all():
            download_groups_task(profile)

        screenshots = set(FacebookGroup.objects.exclude(screenshot__isnull=True).all())
        groups_folder = "groups_screenshots"
        screenshots_folder = Path(settings.MEDIA_ROOT).joinpath(groups_folder)

        for file in os.listdir(screenshots_folder):
            current_file = f"{groups_folder}/{file}"
            if current_file not in screenshots:
                default_storage.delete(current_file)
