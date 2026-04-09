import asyncio
import logging

import ollama
from llama_index.core.memory import StaticMemoryBlock, Memory
from llama_index.llms.ollama import Ollama
from workflows import Context

from scripts.automations import WhatsAppAgent

host = "https://ia.pavelcode5426.duckdns.org"
model_name = "llama3.1:8b-instruct-q4_K_M"
ollama.Client(host).pull(model_name)

logging.basicConfig(level=logging.INFO)
llm = Ollama(model=model_name, base_url=host, request_timeout=120, temperature=0.1, context_window=20_000)
whatsapp_agent = WhatsAppAgent(llm=llm, system_prompt="""
Eres un agente de inteligencia artificial cuyo rol es vender pizzas. 
Tu objetivo es persuadir al cliente para que compre una pizza resaltando 
sus sabores, ingredientes frescos y promociones disponibles. 
Habla de manera amigable, entusiasta y persuasiva, usando descripciones 
apetitosas y transmitiendo urgencia cuando sea necesario. 
Nunca inventes promociones falsas ni des información incorrecta. 
Tu meta final es lograr que el cliente se decida a comprar una pizza.
""")

menu = """"
Clásica Margarita - $6.50
Ingredientes: tomate fresco, mozzarella, albahaca

Volcán de Pepperoni - $7.80
Ingredientes: mozzarella fundida, salsa de tomate, abundante pepperoni

Cuatro Estaciones - $8.20
Ingredientes: jamón, champiñones, alcachofas, aceitunas negras

Fuego BBQ - $9.00
Ingredientes: pollo marinado, cebolla caramelizada, salsa barbacoa, mozzarella

Mediterránea Verde - $7.50
Ingredientes: espinaca, pimientos, aceitunas, queso feta, tomate

Dulce Tentación - $8.90
Ingredientes: mozzarella, jamón, piña fresca, toque de miel

Suprema Carnívora - $10.50
Ingredientes: carne molida, pepperoni, salchicha italiana, panceta

Trufa Elegante - $12.00
Ingredientes: mozzarella, champiñones portobello, aceite de trufa, parmesano

"""
static_memory_block = StaticMemoryBlock(name="menu", static_content=menu, priority=1, description="")
memory = Memory.from_defaults(token_limit=1000, memory_blocks=[static_memory_block])


async def main():
    agent = whatsapp_agent.agent
    ctx = Context(agent)
    while True:
        query = input("Tu:")
        if query == "q":
            break
        if query != "":
            # response = await agent.chat(query)
            response = await agent.run(query, ctx=ctx, memory=memory)
            print(response)


asyncio.run(main())
