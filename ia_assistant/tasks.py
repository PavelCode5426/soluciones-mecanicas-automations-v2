import asyncio

from django.conf import settings
from django.core.cache import cache
from llama_index.core.workflow import Context

from ia_assistant.services import SolucionesHeviaIAService
from services import WAHAService


def reply_whatsapp_message(message, account_id):
    ia_service = cache.get_or_set('seller_agent', SolucionesHeviaIAService())
    agent = ia_service.get_seller_agent()

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
            async with asyncio.timeout(settings.IA_TIMEOUT):
                result = await agent.run(message, ctx=ctx)
                WAHAService.send_text(account_id, str(result))
        finally:
            typing_task.cancel()

        cache.set(account_id, ctx.to_dict())

    if '--reset' in message:
        cache.delete(account_id)
        WAHAService.send_text(account_id, "Memoria borrada....")
    else:
        asyncio.run(main(), debug=True)
