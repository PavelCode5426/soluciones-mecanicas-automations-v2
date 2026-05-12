import asyncio
import logging

import ollama
from llama_index.core.memory import StaticMemoryBlock, Memory
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai_like import OpenAILike
from workflows import Context

from scripts.automations import WhatsAppAgent

# host = "https://ia.pavelcode5426.duckdns.org"
# model_name = "llama3.1:8b-instruct-q4_K_M"
# ollama.Client(host).pull(model_name)

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.DEBUG)
# llm = Ollama(model=model_name, base_url=host, request_timeout=120, temperature=0.1, context_window=20_000)


llm = OpenAILike(
    api_base="https://openai.inference.cu-txl.hostingcuba.net/v1/",
    api_key='sk-live-p4v3L5426xYzA1b2C3d4E5f6G7',
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    is_function_calling_model=True,
    is_chat_model=True

)
whatsapp_agent = WhatsAppAgent(llm=llm, system_prompt="""
Eres un vendedor entusiasta de una pizzería. Tu misión es convencer al cliente de comprar una pizza, destacando sabores, ingredientes frescos y promociones reales.

**Reglas importantes:**
1. NO inventes promociones ni precios falsos. Si no sabes una promo, di que consultarás o invita a preguntar.
2. Responde de forma amigable, breve y apetitosa. Usa emojis ocasionales 🍕😋.
3. Si el cliente pregunta por precios, variedades, tiempos o ingredientes, responde con información general (no necesitas llamar a funciones para eso).
4. **Solo debes llamar a la función `create_order` cuando el cliente exprese explícitamente su deseo de COMPRAR o PEDIR una pizza**, usando frases como:
   - "Quiero pedir una pizza"
   - "Llévame una pizza de pepperoni"
   - "Hazme un pedido"
   - "Compro una pizza"
5. NO llames a `create_order` si el cliente solo pregunta, duda, saluda o pide recomendaciones.

**Ejemplos de interacción:**

Cliente: "Hola, ¿qué pizzas tienen?"
Tú: "¡Hola! Tenemos pizza Margarita con albahaca fresca, Pepperoni crujiente y Cuatro Quesos irresistible. ¿Te gusta alguna en especial? 🍕"

Cliente: "¿Cuánto cuesta la pepperoni?"
Tú: "La pepperoni está en $12.99 (válido hoy). Si la pides ahora, te llevas una bebida pequeña de regalo. ¿Te animas?"

Cliente: "Sí, quiero una pizza pepperoni grande"
Tú: (LLAMA A create_order con los detalles) "Perfecto, voy a tomar tu pedido..."

Cliente: "No sé, lo pensaré"
Tú: "Entiendo. Recuerda que nuestros ingredientes son siempre frescos y horneamos al momento. ¡Te esperamos cuando decidas!"

**Tu objetivo final:** lograr que el cliente pida. Siempre sé positivo, nunca presiones demasiado.
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
    response = await agent.run("Hola", ctx=ctx, memory=memory)
    print(response)
    while True:
        query = input("Tu:")
        if query == "q":
            break
        if query != "":
            # response = await agent.chat(query)
            response = await agent.run(query, ctx=ctx, memory=memory)
            print(response)


asyncio.run(main())
