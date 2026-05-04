from django.db.models import Q
from django.utils.timezone import localtime
from django_q.tasks import async_task

from facebook.models import FacebookPostCampaign, FacebookAgent, FacebookRealAccount
from facebook.tasks import enqueue_lead_explorer, enqueue_facebook_campaign
from services.automations import RealAccountAutomationService


def check_profile_status():
    accounts = FacebookRealAccount.objects.filter(active=True).all()
    for account in accounts:
        service = RealAccountAutomationService(account)
        async_task(service.check_status, task_name=f'check_status', group='check_status', cluster='high_priority')
    return "Comprobación de estado agendada correctamente"


def enqueue_active_agents():
    leads_explorers = FacebookAgent.objects.filter(active=True).order_by('?').all()
    for explorer in leads_explorers:
        enqueue_lead_explorer(explorer)
    return f"Agendados {leads_explorers.count()} agentes comerciales"


def enqueue_active_facebook_campaigns():
    current_time = localtime()
    current_hour = current_time.hour
    posts = (FacebookPostCampaign.objects.select_related('profile')
             .filter(active=True, profile__active=True, from_date__lte=current_time)
             .filter(Q(until_date__gte=current_time) | Q(until_date__isnull=True))
             .filter(schedules__time__hour=current_hour)
             .order_by('?').all())

    total_items = enqueue_facebook_campaign(posts)
    return f"Agendadas {total_items} publicaciones"
