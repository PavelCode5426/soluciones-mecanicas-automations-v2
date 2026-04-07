from django.db.models import Manager


class ProcessedLeadManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(processed=True)
