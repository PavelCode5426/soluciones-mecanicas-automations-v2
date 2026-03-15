import random

from django.db.models import QuerySet
from django_q.tasks import async_task

from facebook.models import FacebookGroup, FacebookProfile, FacebookPost, FacebookLeadExplorer
from services.automations import FacebookAutomationService


def download_groups_task(user):
    service = FacebookAutomationService(user)
    groups = service.get_all_groups()

    for group in groups:
        FacebookGroup.objects.update_or_create(defaults={"name": group['name']},
                                               create_defaults=group, url=group['url'], profile=user)

    return groups


def check_profile_status():
    users = FacebookProfile.objects.filter(active=True).all()
    for user in users:
        service = FacebookAutomationService(user)
        async_task(service.check_status, task_name=f'check_status', group='check_status', cluster='high_priority')
    return "Comprobación de estado agendada correctamente"


def enqueue_posts(posts: QuerySet[FacebookPost]):
    total_items = 0
    for post in posts:
        service = FacebookAutomationService(post.profile)
        groups = FacebookGroup.objects.filter(active=True, categories__posts=post).order_by('?').all()
        for_enqueue = []

        if post.distribution_count:
            groups = groups[:post.distribution_count]
        for group in groups:
            task_name = f"{group.name} -> Post:{post.id}"
            for_enqueue.append(dict(
                args=(group, post,),
                kwargs=dict(task_name=task_name, group=f'facebook_post_{post.id}')
            ))

        random.shuffle(for_enqueue)
        for task in for_enqueue:
            async_task(service.create_post, *task['args'], **task['kwargs'])

        total_items += len(for_enqueue)

    return total_items


def enqueue_active_facebook_posts():
    posts = FacebookPost.objects.select_related('profile').filter(active=True).order_by('?').all()
    total_items = enqueue_posts(posts)
    return f"Agendadas {total_items} publicaciones"


def enqueue_lead_explorer(explorer: FacebookLeadExplorer):
    service = FacebookAutomationService(explorer.profile)
    task_name = f"Leads Explorer {explorer.profile}"
    group_name = f'facebook_leads_explorer_{explorer.profile}'
    async_task(service.group_lead_explorer, explorer, task_name=task_name, group=group_name)


def enqueue_active_lead_explorers():
    leads_explorers = FacebookLeadExplorer.objects.filter(active=True).order_by('?').all()
    for explorer in leads_explorers:
        enqueue_lead_explorer(explorer)
    return "OK"
