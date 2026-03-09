import asyncio

from django.core.management.base import BaseCommand
from llama_index.core.agent import AgentStream
from llama_index.core.workflow import Context

from ia_assistant.factories import create_agent_workflow
from ia_assistant.models import AgentWorkflow


class Command(BaseCommand):
    help = "Hablar con la IA"
    agent_name = 'seller_agent'

    def handle(self, *args, **options):
        agent = create_agent_workflow(AgentWorkflow.objects.first())

        async def main():
            ctx = Context(agent)
            while True:
                query = input("Tu:")
                if query == "q":
                    break
                if query != "":
                    response = await agent.run(query, ctx=ctx)
                    print(response)

        asyncio.run(main(), debug=True)
