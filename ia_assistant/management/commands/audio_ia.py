import asyncio

import tiktoken
from django.core.management.base import BaseCommand
from llama_index.core import Settings
from llama_index.core.callbacks import TokenCountingHandler, CallbackManager
from llama_index.core.workflow import Context

from ia_assistant.factories import create_agent_workflow
from ia_assistant.models import AgentWorkflow
import pyttsx3


class Command(BaseCommand):
    help = "Hablar con la IA"
    agent_name = 'seller_agent'

    def handle(self, *args, **options):
        tokenizer = tiktoken.get_encoding('cl100k_base')
        token_counter = TokenCountingHandler(tokenizer=tokenizer.encode, verbose=True)
        Settings.callback_manager = CallbackManager([token_counter])

        agent = create_agent_workflow(AgentWorkflow.objects.first())

        async def main():
            token_counter.reset_counts()
            ctx = Context(agent)
            engine = pyttsx3.init()
            while True:

                query = input("Tu: ")
                if query == "q":
                    break
                if query != "":
                    response = await agent.run(query, ctx=ctx)
                    engine.say(response)
                    engine.runAndWait()
                    print(f"Respuesta: {response}")
                    print(f"Tokens de prompt: {token_counter.prompt_llm_token_count}")
                    print(f"Tokens de completion: {token_counter.completion_llm_token_count}")
                    print(f"Total de tokens: {token_counter.total_llm_token_count}")
                    input("Esperando...")

        asyncio.run(main(), debug=True)
