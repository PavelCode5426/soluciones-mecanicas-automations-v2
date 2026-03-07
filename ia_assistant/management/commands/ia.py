import asyncio

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from llama_index.core.agent import AgentStream
from llama_index.core.workflow import Context

from ia_assistant.models import Agent
from ia_assistant.services import SolucionesHeviaIAService


class Command(BaseCommand):
    help = "Hablar con la IA"
    agent_name = 'seller_agent'

    def handle(self, *args, **options):
        agent = cache.get_or_set(self.agent_name, Agent.objects.get(name=self.agent_name))
        func_agent = SolucionesHeviaIAService().get_agent(agent)

        async def main():
            ctx = Context(func_agent)
            while True:
                query = input("Tu:")
                if query == "q":
                    break
                if query != "":
                    handler = func_agent.run(query, ctx=ctx)
                    async for event in handler.stream_events():
                        if isinstance(event, AgentStream):
                            if event.response:
                                print(event.response, flush=True)

        asyncio.run(main(), debug=True)
