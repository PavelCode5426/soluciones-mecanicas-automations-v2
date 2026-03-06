import asyncio
import logging

from llama_index.core.agent import AgentWorkflow
from llama_index.core.workflow import Context

from services import SolucionesMecanicasAPIServices

host = 'https://ia.pavelcode5426.duckdns.org'

soluciones_hevia_services = SolucionesMecanicasAPIServices()
soluciones_hevia_services.get_all_products()






agent = AgentWorkflow(agents=[], verbose=True)


async def main():
    logging.basicConfig(level=logging.DEBUG)
    ctx = Context(agent)
    while True:
        query = input("Tu:")
        if query == "q":
            break
        if query != "":
            response = await agent.run(query, ctx=ctx)
            print(response)

# Ejecutar el bucle asíncrono


asyncio.run(main())
