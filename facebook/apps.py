from django.apps import AppConfig


class FacebookConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "facebook"

    def ready(self):
        from django_q.tasks import schedule, Schedule
        # Schedule.objects.all().delete()

        # schedule(func='facebook.tasks.enqueue_active_facebook_posts',
        #          name='enqueue_active_facebook_posts',
        #          repeats=-1,
        #          schedule_type=Schedule.MINUTES,
        #          minutes=1)
