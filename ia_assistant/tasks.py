import asyncio

from django.conf import settings
from django.core.cache import cache
from llama_index.core.agent import AgentStream
from llama_index.core.workflow import Context

from ia_assistant.factories import create_agent_workflow
from ia_assistant.models import AgentWorkflow
from services import WAHAService

AGENT_WORKFLOWS = {}


def __get_or_set_agent_function(agent_workflow: AgentWorkflow):
    name = agent_workflow.name
    func_agent = AGENT_WORKFLOWS.get(name)
    if not func_agent:
        func_agent = create_agent_workflow(agent_workflow)
        AGENT_WORKFLOWS.setdefault(name, func_agent)
    return func_agent


def ___keep_typing_loop_task(service: WAHAService, account_id):
    async def __keep_typing():
        try:
            while True:
                service.start_typing(account_id)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            service.stop_typing(account_id)

    return asyncio.create_task(__keep_typing())


def reply_whatsapp_message(workflow_name, message, account_id):
    whatsapp_service = WAHAService.initialize_using_config()
    agent = cache.get_or_set(workflow_name, AgentWorkflow.objects.get(name=workflow_name))
    workflow = __get_or_set_agent_function(agent)

    async def main():
        previus_context = cache.get_or_set(account_id, {})
        ctx = Context(workflow, previous_context=previus_context)
        typing_task = ___keep_typing_loop_task(whatsapp_service, account_id)
        try:
            async with asyncio.timeout(settings.IA_TIMEOUT):
                response = await workflow.run(message, ctx=ctx)
                whatsapp_service.send_text(account_id, response)
                """"
                async for event in response.stream_events():
                    if isinstance(event, AgentStream):
                        print(event.response, flush=True)
                        # whatsapp_service.send_text(account_id, event.response)
                """
        finally:
            typing_task.cancel()
        cache.set(account_id, ctx.to_dict())

    if '--reset' in message:
        cache.delete(account_id)
        whatsapp_service.send_text(account_id, "Memoria borrada....")
    else:
        asyncio.run(main(), debug=True)
