import asyncio
import logging

from llama_index.core.agent import AgentWorkflow, AgentStream
from llama_index.core.workflow import Context

from services import SolucionesMecanicasAPIServices

host = 'https://ia.pavelcode5426.duckdns.org'

agent = AgentWorkflow(agents=[])


async def main():
    logging.basicConfig(level=logging.DEBUG)
    ctx = Context(agent)
    while True:
        query = input("Tu:")
        if query == "q":
            break
        if query != "":
            handler = agent.run(query)
            async for event in handler.stream_events():
                if isinstance(event, AgentStream):
                    print(event.delta, end="", flush=True)


asyncio.run(main())
