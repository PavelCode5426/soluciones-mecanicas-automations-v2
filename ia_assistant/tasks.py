import asyncio

from django.conf import settings
from django.core.cache import cache
from llama_index.core.workflow import Context

from ia_assistant.factories import create_agent_workflow, create_function_agent
from ia_assistant.models import AgentWorkflow, RAGApplication
from services.whatsapp import WAHAService

AGENT_WORKFLOWS_FUNTIONS = {}


def __get_or_set_rag_agent(agent):
    name = agent.name
    func_agent = AGENT_WORKFLOWS_FUNTIONS.get(name)
    if not func_agent:
        func_agent = create_agent_workflow(agent) if isinstance(agent, AgentWorkflow) else create_function_agent(agent)
        # AGENT_WORKFLOWS.setdefault(name, func_agent)
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


def reply_whatsapp_message(rag_name, message, account_id):
    rag = cache.get_or_set(rag_name, RAGApplication.objects.get(name=rag_name))
    whatsapp_service = WAHAService.initialize_using_rag(rag)
    agent = rag.root_agent or rag.root_workflow
    agent_workflow = __get_or_set_rag_agent(agent)

    async def main():
        previus_context = cache.get_or_set(account_id, {})
        ctx = Context(agent_workflow, previous_context=previus_context)
        typing_task = ___keep_typing_loop_task(whatsapp_service, account_id)
        try:
            async with asyncio.timeout(settings.LLAMAINDEX_TIMEOUT):
                response = await agent_workflow.run(message, ctx=ctx)
                whatsapp_service.send_text(account_id, str(response))
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
