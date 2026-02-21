import asyncio
from pathlib import Path

import ollama
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from llama_index.core.agent import AgentWorkflow, ReActAgent, FunctionAgent
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.core.workflow import Context
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
import logging

host = 'https://ia.pavelcode5426.duckdns.org'

BASE_DIR = Path(__file__).resolve().parent
PERSIST_DIR = BASE_DIR / 'persistent'
DATA_DIR = BASE_DIR / 'data'

system_prompt = """
Eres Emily, una vendedora amable y profesional de Soluciones Hevia, una tienda de autopartes y herramientas mecánicas.

INFORMACIÓN DE LA TIENDA:
- Nombre: Soluciones Hevia
- Web: www.solucioneshevia.com
- Teléfono: +53 54266836
- Dirección: Santa Emilia 210 e/ Flores y Serrano
- Contacto: Ing. Michael Hevia Rodriguez

INSTRUCCIONES:
1. Responde SIEMPRE en español, de forma cordial y servicial.
2. Cuando el cliente te salude (hola, buenos días, etc.), responde amablemente y ofrécele ayuda.
3. Para cualquier consulta sobre productos, precios o disponibilidad, DEBES usar la herramienta 'consultar_productos' (o el nombre que le hayas dado). Nunca inventes información.
4. Si el cliente pide información de la tienda (dirección, teléfono), puedes proporcionarla directamente.
5. Mantén un tono positivo y orientado a soluciones.

Ejemplo de respuesta a saludo:
Cliente: "Hola"
Emily: "¡Hola! Soy Emily de Soluciones Hevia. ¿En qué puedo ayudarte hoy? Tenemos una amplia variedad de autopartes y herramientas. ¿Buscas algún producto en especial?"


"""

client = ollama.Client(host=host)
client.pull('llama3.1:8b-instruct-q4_K_M')
# client.delete("embeddinggemma:latest")
# client.delete("mistral:7b-instruct")


Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text:latest", base_url=host)
Settings.llm = Ollama(base_url=host, model="llama3.1:8b-instruct-q4_K_M", request_timeout=360.0, context_window=8000,
                      temperature=0.0)

if PERSIST_DIR.exists():
    storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
    vector_index = load_index_from_storage(storage_context)
else:
    reader = SimpleDirectoryReader(input_dir=str(DATA_DIR))
    documents = reader.load_data(True)
    parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = parser.get_nodes_from_documents(documents)
    vector_index = VectorStoreIndex(nodes)
    vector_index.storage_context.persist(PERSIST_DIR)

vector_query_engine = vector_index.as_query_engine(response_mode=ResponseMode.COMPACT, similarity_top_k=10)
vector_tool = QueryEngineTool.from_defaults(
    query_engine=vector_query_engine,
    name="consultar_productos",
    description="Utiliza esta herramienta para obtener información sobre productos y precios. Pasa la consulta del cliente tal cual."
)

# SELECCIONA EL MEJOR QUERY ENGINE PARA LO QUE SE VAYA A HACER.
# query_engine = RouterQueryEngine(selector=LLMSingleSelector.from_defaults(), query_engine_tools=[vector_tool])
# query_engine_tool = QueryEngineTool.from_defaults(
#     query_engine=query_engine, name='informacion',
#     description="""
#     Util para responder informacion sobre la empresa o precios. Si te preguntan informacion de precios, productos o la empresa usa la herramienta 'consultar_precios'
#     """
# )
# agent_tools_or_functions = [query_engine_tool]

agent_tools_or_functions = [vector_tool]

seller_agent = FunctionAgent(
    name='seller_agent',
    description="Encagado de responder informacion de la tienda y productos.",
    verbose=True,
    tools=agent_tools_or_functions, system_prompt=system_prompt
)
agent = AgentWorkflow(agents=[seller_agent], root_agent=seller_agent.name, verbose=True)


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
