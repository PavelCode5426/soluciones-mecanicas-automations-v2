import asyncio

from django.conf import settings
from django.core.cache import cache
from llama_index.core.agent import AgentStream
from llama_index.core.workflow import Context

from ia_assistant.models import Agent
from ia_assistant.services import SolucionesHeviaIAService
from services import WAHAService

AGENTS_FUNCTION = {}


def ___keep_typing_loop_task(service: WAHAService, account_id):
    async def __keep_typing():
        try:
            while True:
                service.start_typing(account_id)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            service.stop_typing(account_id)

    return asyncio.create_task(__keep_typing())


def reply_whatsapp_message(agent_name, message, account_id):
    agent = cache.get_or_set(agent_name, Agent.objects.get(name=agent_name))
    whatsapp_service = WAHAService.initialize_using_config()

    func_agent = AGENTS_FUNCTION.get(agent_name)
    if not func_agent:
        service = SolucionesHeviaIAService()
        func_agent = service.get_agent(agent)
        AGENTS_FUNCTION.setdefault(agent_name, func_agent)

    async def main():
        previus_context = cache.get_or_set(account_id, {})
        ctx = Context(func_agent, previous_context=previus_context)
        typing_task = ___keep_typing_loop_task(whatsapp_service, account_id)
        try:
            async with asyncio.timeout(settings.IA_TIMEOUT):
                handler = func_agent.run(message, ctx=ctx)
                async for event in handler.stream_events():
                    if isinstance(event, AgentStream):
                        whatsapp_service.send_text(account_id, event.response)
                whatsapp_service.send_text(account_id, await handler)

        finally:
            typing_task.cancel()
        cache.set(account_id, ctx.to_dict())

    if '--reset' in message:
        cache.delete(account_id)
        whatsapp_service.send_text(account_id, "Memoria borrada....")
    else:
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(main())
        asyncio.run(main(), debug=True)
