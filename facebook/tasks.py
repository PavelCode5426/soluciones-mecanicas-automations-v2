import random

from django.db.models import QuerySet
from django_q.tasks import async_task

from facebook.models import FacebookGroup, FacebookProfile, FacebookPostCampaign, FacebookLeadExplorer
from services.automations import FacebookAutomationService


def syncronize_profile_groups(profile: FacebookProfile):
    service = FacebookAutomationService(profile)
    groups = service.get_all_groups()

    for group in groups:
        FacebookGroup.objects.update_or_create(defaults={"name": group['name']},
                                               create_defaults=group, url=group['url'], profile=profile)

    return groups


def enqueue_lead_explorer(explorer: FacebookLeadExplorer):
    service = FacebookAutomationService(explorer.profile)
    task_name = f"Leads Explorer {explorer.profile}"
    group_name = f'facebook_leads_explorer_{explorer.profile}'
    async_task(service.group_lead_explorer, explorer, task_name=task_name, group=group_name)


def enqueue_facebook_campaign(posts: QuerySet[FacebookPostCampaign]):
    total_items = 0
    for post in posts:
        for_enqueue = []
        service = FacebookAutomationService(post.profile)
        groups = FacebookGroup.objects.filter(active=True, categories__campaigns=post).order_by('?').all()

        if post.distribution_count:
            groups = groups[:post.distribution_count]
        for group in groups:
            task_name = f"{group.name}| {post.id} | {post.profile}"
            for_enqueue.append(
                {
                    "args": (group, post,),
                    "kwargs": {"task_name": task_name, "group": f'facebook_campaign_{post.id}'}
                }
            )

            random.shuffle(for_enqueue)
            for task in for_enqueue:
                async_task(service.publish_new_campaign, *task['args'], **task['kwargs'])

            total_items += len(for_enqueue)

        return total_items
