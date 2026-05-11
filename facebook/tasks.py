import itertools
import random

from django.db.models import QuerySet
from django_q.tasks import async_task

from facebook.models import FacebookGroup, FacebookPostCampaign, FacebookAgent, FacebookRealAccount, \
    FacebookAccountGroup, FacebookProfileGroup, FacebookScheduledPost
from services.automations import RealAccountAutomationService


def syncronize_account_groups(account: FacebookRealAccount):
    service = RealAccountAutomationService(account)
    groups = service.get_all_groups()
    profiles = account.profiles.all()

    for group in groups:
        group, _ = FacebookGroup.objects.update_or_create(
            defaults={"name": group['name'], "deleted": False}, create_defaults=group, url=group['url']
        )
        FacebookAccountGroup.objects.get_or_create(
            defaults={"group": group, "account": account}, group=group, account=account
        )
        for profile in profiles:
            FacebookProfileGroup.objects.get_or_create(
                defaults={"group": group, "profile": profile}, group=group, profile=profile
            )

    return groups


def join_account_to_groups(account: FacebookRealAccount, groups_urls: list[str]):
    service = RealAccountAutomationService(account)
    service.join_groups(groups_urls)
    syncronize_account_groups(account)


def enqueue_lead_explorer(explorer: FacebookAgent):
    real_account = FacebookRealAccount.objects.filter(active=True, profiles=explorer.profile)
    if explorer.distribution_list:
        real_account = real_account.filter(groups__group__distribution_lists=explorer.distribution_list)
    real_account = real_account.order_by('?').first()
    service = RealAccountAutomationService(real_account)
    task_name = f"agent_{explorer}".lower().replace(" ", "_")
    group_name = f'run_agent_{explorer.profile}'.lower().replace(" ", '_')
    async_task(service.group_lead_explorer, explorer, task_name=task_name, group=group_name, cluster='default')


def enqueue_facebook_campaign(posts: QuerySet[FacebookPostCampaign]):
    total_items = 0
    account_services = {}
    for post in posts:
        for_enqueue = []
        groups = FacebookGroup.objects.filter(
            active=True, distribution_lists__active=True, distribution_lists__campaigns=post,
            real_accounts__account__active=True
        ).order_by('?').all()[:post.distribution_count]

        group_ids = list(groups.values_list('id', flat=True))
        real_accounts = FacebookRealAccount.objects.filter(
            active=True,
            profiles__active=True, profiles__campaigns=post,
            groups__group_id__in=group_ids,
            profiles__groups__active=True,
            profiles__groups__group_id__in=group_ids
        ).order_by('?')

        for group, real_account in zip(groups, itertools.cycle(real_accounts)):
            service = account_services.setdefault(real_account.pk, RealAccountAutomationService(real_account))
            task_name = f"{group.name} | {post.profile}"
            for_enqueue.append(
                {
                    "func": service.publish_new_campaign,
                    "args": (group, post,),
                    "kwargs": {"task_name": task_name, "group": f'facebook_campaign_{post.id}'}
                }
            )

        random.shuffle(for_enqueue)
        for task in for_enqueue:
            async_task(task['func'], *task['args'], **task['kwargs'], cluster="default")
        total_items += len(for_enqueue)

    return total_items


def enqueue_facebook_post(posts: QuerySet[FacebookScheduledPost]):
    total_items = 0
    account_services = {}
    for post in posts:
        for_enqueue = []

        for real_account in post.profile.real_accounts.all():
            service = account_services.setdefault(real_account.pk, RealAccountAutomationService(real_account))
            task_name = f"{post} | {real_account}"
            for_enqueue.append(
                {
                    "func": service.publish_new_post,
                    "args": (post,),
                    "kwargs": {"task_name": task_name, "group": f'facebook_post_{post.id}'}
                }
            )

        random.shuffle(for_enqueue)
        for task in for_enqueue:
            async_task(task['func'], *task['args'], **task['kwargs'], cluster="default")
        total_items += len(for_enqueue)

    return total_items
