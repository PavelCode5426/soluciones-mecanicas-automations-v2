import asyncio
from pathlib import Path

import ollama
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.agent import AgentWorkflow, FunctionAgent
from llama_index.core.workflow import Context
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

host = 'https://ia.pavelcode5426.duckdns.org'

BASE_DIR = Path(__file__).resolve().parent
PERSIST_DIR = BASE_DIR / 'persistent'
DATA_DIR = BASE_DIR / 'data'

system_prompt = """"
Eres un vendedor que responde siempre en español. 
Tu objetivo es responder al cliente como si estuvieras detras del mostrador y garantizar una venta.
No menciones la palabra inventario, refierete a tienda como por ejemplo: 'En nuestra tienda tenemos (piezas) a (precio)'
"""

client = ollama.Client(host=host)
embed_model = OllamaEmbedding(model_name="embeddinggemma:latest", base_url=host)
llm = Ollama(base_url=host, model="mistral:7b-instruct", request_timeout=360.0, context_window=8000,
             system_prompt=system_prompt)

if PERSIST_DIR.exists():
    storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
    index = load_index_from_storage(storage_context, embed_model=embed_model)
else:
    reader = SimpleDirectoryReader(input_dir=str(DATA_DIR))
    documents = reader.load_data(True)
    index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
    index.storage_context.persist(PERSIST_DIR)

query_engine = index.as_query_engine(llm=llm)


def search_products(query: str) -> str:
    """Util para responder preguntas de lenguaje natural acerca de informacion de la empresa y documentos"""
    return str(query_engine.query(query))


agent = AgentWorkflow.from_tools_or_functions(
    tools_or_functions=[search_products],
    system_prompt=system_prompt, llm=llm
)
agent2 = FunctionAgent(
    tools=[search_products],
    system_prompt=system_prompt,
    llm=llm,
)
ctx = Context(agent)


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
