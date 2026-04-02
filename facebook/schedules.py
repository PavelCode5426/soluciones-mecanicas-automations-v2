import random

from django.db.models import QuerySet, Q, ExpressionWrapper, F, DecimalField
from django.utils.timezone import now
from django_q.tasks import async_task

from facebook.models import FacebookGroup, FacebookProfile, FacebookPostCampaign, FacebookLeadExplorer
from facebook.tasks import enqueue_lead_explorer, enqueue_facebook_campaign
from services.automations import FacebookAutomationService


def check_profile_status():
    users = FacebookProfile.objects.filter(active=True).all()
    for user in users:
        service = FacebookAutomationService(user)
        async_task(service.check_status, task_name=f'check_status', group='check_status', cluster='high_priority')
    return "Comprobación de estado agendada correctamente"


def enqueue_active_lead_explorers():
    leads_explorers = FacebookLeadExplorer.objects.filter(active=True).order_by('?').all()
    for explorer in leads_explorers:
        enqueue_lead_explorer(explorer)
    return "OK"


def enqueue_active_facebook_campaigns():
    current_hour = now().hour
    posts = (FacebookPostCampaign.objects.select_related('profile')
             .filter(active=True, from_date__lte=now())
             .filter(Q(until_date__gte=now()) | Q(until_date__isnull=True))
             .annotate(can_publish=ExpressionWrapper(F('frequency') % current_hour, DecimalField()))
             .filter(can_publish=0).order_by('?').all())

    total_items = enqueue_facebook_campaign(posts)
    return f"Agendadas {total_items} publicaciones"
