import asyncio

from django.conf import settings
from django.core.cache import cache
from llama_index.core.workflow import Context

from ia_assistant.models import Agent
from ia_assistant.services import SolucionesHeviaIAService
from services import WAHAService


def reply_whatsapp_message(agent_name, message, account_id):
    agent = cache.get_or_set(agent_name, Agent.objects.get(name=agent_name))

    func_agent = cache.get(f"{agent_name}_function")
    if not func_agent:
        service = SolucionesHeviaIAService()
        func_agent = service.get_agent(agent)
        cache.set(f"{agent_name}_function", func_agent)

    async def keep_typing():
        try:
            while True:
                WAHAService.start_typing(account_id)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            WAHAService.stop_typing(account_id)

    async def main():
        previus_context = cache.get_or_set(account_id, {})
        ctx = Context(func_agent, previous_context=previus_context)
        typing_task = asyncio.create_task(keep_typing())
        try:
            async with asyncio.timeout(settings.IA_TIMEOUT):
                result = await func_agent.run(message, ctx=ctx)
                WAHAService.send_text(account_id, str(result))
        finally:
            typing_task.cancel()

        cache.set(account_id, ctx.to_dict())

    if '--reset' in message:
        cache.delete(account_id)
        WAHAService.send_text(account_id, "Memoria borrada....")
    else:
        asyncio.run(main(), debug=True)
