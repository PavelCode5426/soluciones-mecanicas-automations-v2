import importlib

from llama_index.core.agent import FunctionAgent, AgentWorkflow
from llama_index.core.tools import FunctionTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

from ia_assistant import models


def create_llm(model: models.OllamaLLM):
    return Ollama(model=model.model_name, base_url=model.base_url, **model.config)


def create_embedding_model(model: models.OllamaLLM):
    return OllamaEmbedding(model_name=model.name, base_url=model.base_url)


def create_function_agent(agent: models.Agent):
    tools = []
    for tool in models.FunctionTool.objects.filter(agent=agent, active=True).all():
        module, func = tool.function.rsplit('.', 1)
        module = importlib.import_module(module)
        tools.append(FunctionTool.from_defaults(getattr(module, func), name=tool.name, description=tool.description))

    llm = create_llm(agent.llm)
    return FunctionAgent(name=agent.name, description=agent.description,
                         system_prompt=agent.system_prompt, tools=tools, llm=llm, **agent.options)


def create_agent_workflow(workflow: models.AgentWorkflow):
    agents = [create_function_agent(agent) for agent in workflow.agents.filter(active=True).all()]
    return AgentWorkflow(agents=agents, root_agent=workflow.root_agent.name, **workflow.options)
