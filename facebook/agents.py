from typing import Optional

import chromadb
from llama_index.core import StorageContext, load_index_from_storage, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import StaticMemoryBlock, FactExtractionMemoryBlock, VectorMemoryBlock, Memory, \
    InsertMethod
from llama_index.core.tools import FunctionTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore


class PersonalizedFacebookAccount:
    llm: Ollama
    embed_model: OllamaEmbedding
    chroma_client: chromadb.PersistentClient

    DOCS_DIR: Optional[str]
    CONTEXT_STORE_DIR: Optional[str]

    def __init__(self, llm, embed_model, chroma_client, DOCS_DIR, CONTEXT_STORE_DIR):
        self.llm = llm
        self.embed_model = embed_model
        self.chroma_client = chroma_client
        self.DOCS_DIR = DOCS_DIR
        self.CONTEXT_STORE_DIR = self.CONTEXT_STORE_DIR

    def create_memory(self):
        personality_content = "Tengo personalidad de un niño de 10 años."
        collection = self.chroma_client.get_or_create_collection('memory_vector')
        vector_store = ChromaVectorStore(chroma_collection=collection)

        static_block = StaticMemoryBlock(name="personality", static_content=personality_content, priority=0)
        facts_block = FactExtractionMemoryBlock(name="user_facts", llm=self.llm, priority=1)
        vector_block = VectorMemoryBlock(
            name="history_search", vector_store=vector_store, embed_model=self.embed_model, similarity_top_k=3,
            priority=2)

        memory_blocks = [static_block, facts_block, vector_block]
        return Memory.from_defaults(token_limit=40000, memory_blocks=memory_blocks, insert_method=InsertMethod.USER)

    def __knowledge_vector_index(self):
        collection_name = "knowledge_vectors"
        if any(collection_name == collection.name for collection in self.chroma_client.list_collections()):
            collection = self.chroma_client.get_collection(collection_name)
            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store,
                persist_dir=self.CONTEXT_STORE_DIR
            )
            index = load_index_from_storage(storage_context, embed_model=self.embed_model)
        else:
            documents = SimpleDirectoryReader(input_dir=self.DOCS_DIR).load_data()

            collection = self.chroma_client.create_collection(collection_name)
            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex.from_documents(
                documents=documents, embed_model=self.embed_model,
                storage_context=storage_context
            )

            storage_context.persist(self.CONTEXT_STORE_DIR)
        return index

    def create_new_post(self, post_topic: str):
        """"Utiliza esta funcion para crear una nueva publicación."""
        knowledge_vector_index = self.__knowledge_vector_index().as_query_engine(self.llm, similarity_top_k=4)
        return knowledge_vector_index.query(post_topic)

    async def query(self, query: str):
        system_prompt = "Eres un asistente. Usa tu personalidad para responder con el tono adecuado."
        memory = self.create_memory()
        agent = FunctionAgent(llm=self.llm, system_prompt=system_prompt, tools=[
            FunctionTool.from_defaults(self.create_new_post)
        ])

        return await agent.run(query, memory=memory)
