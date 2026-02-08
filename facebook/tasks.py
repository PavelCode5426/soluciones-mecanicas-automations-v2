import random

from django_q.tasks import async_task

from facebook.models import FacebookGroup, FacebookProfile, FacebookPost
from facebook.services import FacebookAutomationService


def download_groups_task(user):
    service = FacebookAutomationService(user)
    groups = service.get_all_groups()

    for group in groups:
        FacebookGroup.objects.update_or_create(defaults={"name": group['name']},
                                               create_defaults=group, url=group['url'])

    return groups


def check_profile_status():
    users = FacebookProfile.objects.all()
    for user in users:
        service = FacebookAutomationService(user)
        async_task(service.check_status, task_name=f'check_status', group='check_status', cluster='high_priority')
    return "Comprobación de estado agendada correctamente"


def enqueue_posts(user: FacebookProfile, posts: list[FacebookPost]):
    service = FacebookAutomationService(user)
    for_enqueue = []
    for post in posts:
        groups = FacebookGroup.objects.filter(active=True, categories__posts=post).order_by('?').all()
        for group in groups:
            task_name = f"{group.name} -> Post:{post.id}"
            for_enqueue.append(dict(
                args=(group, post,),
                kwargs=dict(task_name=task_name, group=f'facebook_post_{post.id}')
            ))

    total_items = len(for_enqueue)
    random.shuffle(for_enqueue)
    for task in for_enqueue:
        async_task(service.create_post, *task['args'], **task['kwargs'])

    return total_items


def enqueue_active_facebook_posts():
    # if Task.objects.filter(group='enqueue_active_facebook_posts', attempt_count=0).count() == 0:
    total_items = 0
    users = FacebookProfile.objects.all()
    posts = FacebookPost.objects.filter(active=True).order_by('?').all()
    for user in users:
        total_items += enqueue_posts(user, posts)
    return f"Agendadas {total_items} publicaciones"
