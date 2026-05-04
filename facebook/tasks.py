import random

from django.db.models import QuerySet
from django_q.tasks import async_task

from facebook.models import FacebookGroup, FacebookPostCampaign, FacebookAgent, FacebookRealAccount, \
    FacebookAccountGroup, FacebookProfileGroup
from services.automations import FacebookAutomationService, RealAccountAutomationService


def syncronize_account_groups(account: FacebookRealAccount):
    service = RealAccountAutomationService(account)
    groups = service.get_all_groups()
    profiles = account.profiles.all()

    for group in groups:
        group, _ = FacebookGroup.objects.update_or_create(
            defaults={"name": group['name']}, create_defaults=group, url=group['url']
        )
        FacebookAccountGroup.objects.get_or_create(
            defaults={"group": group, "account": account}, group=group, account=account
        )
        for profile in profiles:
            FacebookProfileGroup.objects.get_or_create(
                defaults={"group": group, "profile": profile}, group=group, profile=profile
            )

    return groups


def enqueue_lead_explorer(explorer: FacebookAgent):
    service = FacebookAutomationService(explorer.profile)
    task_name = f"agent_{explorer}".lower().replace(" ", "_")
    group_name = f'run_agent_{explorer.profile}'.lower().replace(" ", '_')
    async_task(service.group_lead_explorer, explorer, task_name=task_name, group=group_name, cluster='default')


def enqueue_facebook_campaign(posts: QuerySet[FacebookPostCampaign]):
    total_items = 0
    for post in posts:
        for_enqueue = []
        groups = FacebookGroup.objects.filter(
            active=True, distribution_lists__active=True, distribution_lists__campaigns=post,
        ).order_by('?').all()[:post.distribution_count]

        real_account = FacebookRealAccount.objects.filter(
            active=True,
            profiles__active=True, profiles__campaigns=post,
            groups__group__in=groups,
            profiles__profile_groups__active=True,
            profiles__profile_groups__group__in=groups
        ).order_by('?').first()

        service = RealAccountAutomationService(real_account)
        for group in groups:
            task_name = f"{group.name} | {post.profile}"
            for_enqueue.append(
                {
                    "args": (group, post,),
                    "kwargs": {"task_name": task_name, "group": f'facebook_campaign_{post.id}'}
                }
            )

        random.shuffle(for_enqueue)
        for task in for_enqueue:
            async_task(service.publish_new_campaign, *task['args'], **task['kwargs'], cluster="default")
        total_items += len(for_enqueue)

    return total_items
