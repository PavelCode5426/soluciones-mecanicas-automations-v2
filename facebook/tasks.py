import asyncio
import random

from asgiref.sync import async_to_sync
from django.core.cache import cache
from django_q.tasks import async_task
from llama_index.core.workflow import Context

from facebook.models import FacebookGroup, FacebookProfile, FacebookPost
from facebook.services import FacebookAutomationService, IAService, WAHAService


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
        if post.distribution_count:
            groups = groups[:post.distribution_count]
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


def reply_whatsapp_message(message, account_id, account_name):
    ia_service = IAService()
    agent = ia_service.get_seller_agent_thinker()

    async def keep_typing():
        try:
            while True:
                WAHAService.start_typing(account_id)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            WAHAService.stop_typing(account_id)

    async def main():
        previus_context = cache.get_or_set(account_id, {})
        ctx = Context(agent, previous_context=previus_context)

        typing_task = asyncio.create_task(keep_typing())
        try:
            result = await agent.run(message, ctx=ctx)
            print(result)
            print(str(result))
            WAHAService.send_text(account_id, str(result))
        finally:
            typing_task.cancel()

        cache.set(account_id, ctx.to_dict())

    asyncio.run(main())
