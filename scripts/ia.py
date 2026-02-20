import asyncio
from pathlib import Path

import ollama
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from llama_index.core.agent import AgentWorkflow, ReActAgent
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.core.workflow import Context
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

host = 'https://ia.pavelcode5426.duckdns.org'

BASE_DIR = Path(__file__).resolve().parent
PERSIST_DIR = BASE_DIR / 'persistent'
DATA_DIR = BASE_DIR / 'data'

import logging

logging.basicConfig(level=logging.DEBUG)

s7ystem_prompt = """"
Te llamas Emily, eres una vendedora profesional que atiende al cliente desde un chat en línea. 
Tu objetivo es garantizar la venta ofreciendo información clara, atractiva y convincente basada en los documentos disponibles. 
Habla siempre en español, con tono cordial, persuasivo y seguro. 

Cuando el cliente salude con expresiones simples como "hola" o "buenas tardes", responde con un saludo cálido y breve, preséntate como representante de la tienda y ofrece tu ayuda de manera amable, sin entrar aún en detalles de productos ni precios. 

Cuando el cliente pregunte por productos, precios o características, entonces sí describe lo que tenemos en nuestra tienda, destacando beneficios, ventajas y valor de la compra. 
No menciones la palabra "inventario"; en su lugar, refiérete a "nuestra tienda" y presenta los productos como disponibles para el cliente. 

Adapta tu respuesta al contexto del cliente: 
- Si pregunta por productos informale del precio.
- Si pregunta por precios, recalca la relación calidad-precio. 
- Si pregunta por características, resalta cómo le solucionan una necesidad. 
- Si duda, ofrece alternativas atractivas.

Tu meta es cerrar la venta transmitiendo confianza y profesionalismo. 
Responde siempre de forma firme y sencilla, pero ajusta el nivel de detalle según lo que el cliente pregunte, evitando ser demasiado impulsiva cuando solo saluda.

"""

system_prompt = (
    "Eres Emily, una vendedora en una tienda de autopartes. "
    "Siempre respondes en español, de forma amable y profesional. "
    "Cuando el cliente pregunte por productos o precios, debes usar la herramienta 'consultar_precios' para obtener la información precisa."
)

client = ollama.Client(host=host)
# client.delete("embeddinggemma:latest")
# client.delete("mistral:7b-instruct")


Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text:latest", base_url=host)
Settings.llm = Ollama(base_url=host, model="mistral:7b-instruct", request_timeout=360.0, context_window=8000)

if PERSIST_DIR.exists():
    storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
    vector_index = load_index_from_storage(storage_context)
else:
    reader = SimpleDirectoryReader(input_dir=str(DATA_DIR))
    documents = reader.load_data(True)
    # splitter = SentenceSplitter(chunk_size=200, chunk_overlap=0)
    # nodes = splitter.get_nodes_from_documents(documents)
    # vector_index = VectorStoreIndex(nodes)
    vector_index = VectorStoreIndex.from_documents(documents)
    vector_index.storage_context.persist(PERSIST_DIR)

vector_query_engine = vector_index.as_query_engine(response_mode=ResponseMode.COMPACT, use_async=True)
vector_tool = QueryEngineTool.from_defaults(
    query_engine=vector_query_engine,
    name="consultar_precios",
    description="Utiliza esta herramienta para obtener información sobre productos, precios y disponibilidad. Pasa la consulta del cliente tal cual."
)


# SELECCIONA EL MEJOR QUERY ENGINE PARA LO QUE SE VAYA A HACER.
query_engine = RouterQueryEngine(selector=LLMSingleSelector.from_defaults(), query_engine_tools=[vector_tool])
query_engine_tool = QueryEngineTool.from_defaults(
    query_engine=query_engine, name='informacion',
    description="""
    Util para responder informacion sobre la empresa o precios. Si te preguntan informacion de precios, productos o la empresa usa la herramienta 'consultar_precios'
    """
)

agent_tools_or_functions = [query_engine_tool]

seller_agent = ReActAgent(name='seller_agent',
                          description="Encagado de responder informacion de la tienda y productos.",
                          tools=agent_tools_or_functions, system_prompt=system_prompt)

agent = AgentWorkflow(agents=[seller_agent])
ctx = Context(agent)

faith_evaluator = FaithfulnessEvaluator()
relevancy_evaluator = RelevancyEvaluator()


async def main():
    while True:
        query = input("Tu:")
        if query == "q":
            break
        if query != "":
            response = await agent.run(query, ctx=ctx)
            print(response)


# Ejecutar el bucle asíncrono
asyncio.run(main())
