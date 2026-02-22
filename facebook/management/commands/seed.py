from django.conf.global_settings import AUTH_USER_MODEL
from django.core.management.base import BaseCommand

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

        created, user = AUTH_USER_MODEL.objects.get_or_create(
            default={"username": "pavelcode5426", "isstaff": True, "issuperadmin": True},
            username='pavelcode5426',
        )
        user.set_password('1234')
        user.save()
