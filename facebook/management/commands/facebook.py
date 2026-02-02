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
        dirs, files = self.get_files_and_folders("groups_screenshots")

        for file in files:
            if file not in screenshots:
                default_storage.delete(file)

        for directory in dirs:
            default_storage.delete(directory)

    def get_files_and_folders(self, path=""):
        dirs, files = default_storage.listdir(path)

        for directory in dirs:
            subdirs, subfiles = self.get_files_and_folders(f"{path}/{directory}")
            dirs += subdirs
            files += subfiles
        return dirs, files
