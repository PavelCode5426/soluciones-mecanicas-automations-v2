# def download_groups_task(user):
#     from facebook.services import FacebookAutomationService
#     from concurrent.futures import ThreadPoolExecutor
#
#     facebook = FacebookAutomationService(user)
#     with ThreadPoolExecutor(max_workers=4) as executor:
#         future = executor.submit(facebook.get_all_groups)
#         try:
#             print(future.result())
#         except Exception as e:
#             import traceback
#             traceback.print_exc()


from django_q.tasks import async_task
from facebook.models import FacebookGroup, FacebookProfile, FacebookPost
from facebook.services import FacebookAutomationService


def download_groups_task(user):
    service = FacebookAutomationService(user)
    groups = service.get_all_groups()

    for group in groups:
        FacebookGroup.objects.update_or_create(
            defaults={"name": group['name'], "active": True},
            create_defaults=group,
            url=group['url']
        )


def enqueue_active_facebook_posts():
    user = FacebookProfile.objects.first()
    service = FacebookAutomationService(user)
    posts = FacebookPost.objects.filter(active=True).all()

    for post in posts:
        groups = FacebookGroup.objects.filter(active=True, categories__posts=post).all()
        for group in groups:
            task_name = f"{group.name} -> Post:{post.id}"
            async_task(service.create_post, group, post, task_name=task_name)
