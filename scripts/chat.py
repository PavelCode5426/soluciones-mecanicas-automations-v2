import asyncio
import logging

import chromadb
import ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from workflows import Context

from automations import FacebookAccountAgent

host = "https://ia.pavelcode5426.duckdns.org"
persist_dir = "./agent/context_store_persistence/"
chromadb_dir = "./agent/chroma_db"

# model_name = "llama3.2:1b"
model_name = "llama3.1:8b-instruct-q4_K_M"
embedding_model_name = "embeddinggemma:300m-qat-q4_0"
ollama.Client(host).pull(model_name)

logging.basicConfig(level=logging.INFO)
llm = Ollama(model=model_name, base_url=host, request_timeout=120, temperature=0.1, context_window=4000)
embed_model = OllamaEmbedding(model_name=embedding_model_name, base_url=host)
chroma_client = chromadb.PersistentClient(path=chromadb_dir)

account_agent = FacebookAccountAgent(llm=llm, embed_model=embed_model, chroma_client=chroma_client, DOCS_DIR='./data',
                                     CONTEXT_STORE_DIR=persist_dir)


async def main():
    agent = account_agent.rag
    ctx = Context(account_agent.agent)
    while True:
        query = input("Tu:")
        if query == "q":
            break
        if query != "":
            response = await agent.chat(query)
            # response = await agent.run(query, ctx=ctx)
            print(response)
            # async for event in handler.stream_events():
            #     if isinstance(event, AgentStream):
            #         print(event.delta, end="", flush=True)


asyncio.run(main())
