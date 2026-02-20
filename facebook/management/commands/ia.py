from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import asyncio
from llama_index.core import Settings, StorageContext, load_index_from_storage, VectorStoreIndex, Document
from llama_index.core.agent import ReActAgent, AgentWorkflow
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.workflow import Context
from llama_index.llms.ollama import Ollama
from ollama import Client
import asyncio

from facebook.models import FacebookPost


class Command(BaseCommand):
    help = "Hablar con la IA"

    system_prompt = (
        "Eres Emily, una vendedora en una tienda de autopartes. "
        "Siempre respondes en español, de forma amable y profesional. "
        "Cuando el cliente pregunte por productos o precios, debes usar la herramienta 'consultar_precios' para obtener la información precisa."
    )

    def init_llamaindex(self):
        host = settings.IA_OLLAMA_HOST
        client = Client(host=host)
        Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text:latest", base_url=host)
        Settings.llm = Ollama(base_url=host, model="mistral:7b-instruct", request_timeout=360.0, context_window=8000)

    def get_facebook_post_query_engine(self, reset=False):
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

        return vector_index.as_query_engine(response_mode=ResponseMode.COMPACT, use_async=True)

    def handle(self, *args, **options):
        self.init_llamaindex()
        post_query_engine = self.get_facebook_post_query_engine()
        post_query_engine_tool = QueryEngineTool.from_defaults(
            query_engine=post_query_engine,
            name="consultar_precios",
            description="Utiliza esta herramienta para obtener información sobre productos y precios basandose en publicaciones."
        )

        query_engine = RouterQueryEngine(
            selector=LLMSingleSelector.from_defaults(),
            query_engine_tools=[post_query_engine_tool]
        )
        query_engine_tool = QueryEngineTool.from_defaults(query_engine=query_engine)

        agent_tools_or_functions = [post_query_engine_tool]

        seller_agent = ReActAgent(name='seller_agent',
                                  description="Encagado de responder informacion de la tienda y productos.",
                                  tools=agent_tools_or_functions, system_prompt=self.system_prompt)

        agent = AgentWorkflow(agents=[seller_agent])
        ctx = Context(agent)

        while True:
            query = input("Tu:")
            if query == "q":
                break
            if query != "":
                response = agent.run(query, ctx=ctx)
                while not response.done():
                    self.stdout.write('.')
                self.stdout.write(response)
