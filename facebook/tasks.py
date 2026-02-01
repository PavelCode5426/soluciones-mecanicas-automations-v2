from django_q.models import Task
from django_q.tasks import async_task, count_group
from facebook.models import FacebookGroup, FacebookProfile, FacebookPost
from facebook.services import FacebookAutomationService


def download_groups_task(user):
    service = FacebookAutomationService(user)
    groups = service.get_all_groups()

    FacebookGroup.objects.update(active=False)
    for group in groups:
        FacebookGroup.objects.update_or_create(
            defaults={"name": group['name'], "active": True},
            create_defaults=group,
            url=group['url']
        )
    return groups


def enqueue_active_facebook_posts():
    # if Task.objects.filter(group='enqueue_active_facebook_posts', attempt_count=0).count() == 0:
    user = FacebookProfile.objects.first()
    service = FacebookAutomationService(user)
    posts = FacebookPost.objects.filter(active=True).all()
    total_items = 0

    for post in posts:
        groups = FacebookGroup.objects.filter(active=True, categories__posts=post).all()
        for group in groups:
            task_name = f"{group.name} -> Post:{post.id}"
            async_task(service.create_post, group, post, task_name=task_name, group=f'facebook_post_{post.id}')
        total_items += groups.count()
    return f"Agendadas {total_items} publicaciones"
