import datetime

from django.core.management.base import BaseCommand

from core.models import Schedule


class Command(BaseCommand):
    """script to seed database

    Args:
        BaseCommand (_type_): _description_
    """

    help = "Upgrade the database with data for fix and generate information."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Initializing database.."))
        for x in range(0, 24):
            time = datetime.time(hour=x)
            name = time.strftime('%I:%M %p')
            Schedule.objects.update_or_create(
                defaults={"name": name},
                create_defaults={"name": name, "time": time},
                time=time
            )

        self.stdout.write(self.style.WARNING("done."))
