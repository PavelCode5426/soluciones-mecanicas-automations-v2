from django.core.management.base import BaseCommand

from facebook.models import FacebookProfile
from facebook.tasks import download_groups_task

from django_q.tasks import schedule, Schedule


class Command(BaseCommand):
    help = "Sincroniza la informacion de facebook con la base de datos"

    def handle(self, *args, **options):
        Schedule.objects.all().delete()

        schedule(func='facebook.tasks.enqueue_active_facebook_posts',
                 name='enqueue_active_facebook_posts',
                 repeats=-1,
                 schedule_type=Schedule.MINUTES,
                 minutes=60)