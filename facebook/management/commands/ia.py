import asyncio

from django.core.management.base import BaseCommand
from django.utils import asyncio
from llama_index.core.workflow import Context

from facebook.services import IAService


class Command(BaseCommand):
    help = "Hablar con la IA"

    def handle(self, *args, **options):
        agent = IAService().get_seller_agent()

        async def main():
            ctx = Context(agent)
            while True:
                query = input("Tu:")
                if query == "q":
                    break
                if query != "":
                    response = await agent.run(query, ctx=ctx)
                    print(response)

        asyncio.run(main())
