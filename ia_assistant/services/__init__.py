import importlib
from pathlib import Path

from django.conf import settings
from llama_index.core import Settings, StorageContext, load_index_from_storage, VectorStoreIndex, Document, \
    SimpleDirectoryReader
from llama_index.core.agent import FunctionAgent
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.tools import QueryEngineTool, FunctionTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

from facebook.models import FacebookPost
from ia_assistant.models import Agent, AgentTool


class SolucionesHeviaIAService:
    verbose = True
    embedding_model = 'nomic-embed-text:latest'
    llm_model = 'llama3.1:8b-instruct-q4_K_M'

    def init_llamaindex(self):
        host = settings.IA_OLLAMA_HOST
        Settings.embed_model = OllamaEmbedding(model_name=self.embedding_model, base_url=host)
        Settings.llm = Ollama(base_url=host, model=self.llm_model, request_timeout=60.0,
                              context_window=8000, temperature=0.0)

    def get_facebook_post_query_engine_tool(self, reset=False):
        PERSIST_DIR = settings.IA_POST_PERSISTEN / "post"
        if PERSIST_DIR.exists() and not reset:
            storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
            vector_index = load_index_from_storage(storage_context)
        else:
            documents = []
            posts = FacebookPost.objects.filter(active=True).all()
            for post in posts:
                documents.append(Document(text=post.text))
            vector_index = VectorStoreIndex.from_documents(documents)
            vector_index.storage_context.persist(PERSIST_DIR)

        query_engine = vector_index.as_query_engine(response_mode=ResponseMode.COMPACT, use_async=True)
        return QueryEngineTool.from_defaults(
            query_engine=query_engine,
            name="consultar_precios",
            description="Utiliza esta herramienta para obtener información sobre productos y precios. Pasa la consulta del cliente tal cual."
        )

    def get_products_query_engine_tool_____no_usar(self, reset=False):
        PERSIST_DIR = settings.IA_POST_PERSISTEN / "products"
        if PERSIST_DIR.exists() and not reset:
            storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
            vector_index = load_index_from_storage(storage_context)
        else:
            DATA_DIR = Path(__file__).parent / 'data/products'
            documents = SimpleDirectoryReader(DATA_DIR).load_data()
            # parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
            # nodes = parser.get_nodes_from_documents(documents)
            # vector_index = VectorStoreIndex(nodes)
            vector_index = VectorStoreIndex.from_documents(documents)
            vector_index.storage_context.persist(PERSIST_DIR)

        query_engine = vector_index.as_query_engine(response_mode=ResponseMode.COMPACT, use_async=True,
                                                    similarity_top_k=10)
        return QueryEngineTool.from_defaults(
            query_engine=query_engine,
            name="consultar_precios",
            description="Utiliza esta herramienta para obtener información sobre productos y precios. Pasa la consulta del cliente tal cual."
        )

    def __get_agent_tools(self, agent: Agent):
        tools = []

        for tool in AgentTool.objects.filter(agent=agent, active=True).all():
            funct = importlib.import_module(tool.function)
            tools.append(FunctionTool.from_defaults(funct, name=tool.name, description=tool.description))
        return tools

    def get_agent(self, agent: Agent):
        self.init_llamaindex()

        return FunctionAgent(name=agent.name,
                             verbose=self.verbose,
                             description=agent.description,
                             system_prompt=agent.system_prompt,
                             tools=self.__get_agent_tools(agent))
