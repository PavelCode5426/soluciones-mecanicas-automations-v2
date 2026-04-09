from django.contrib import admin

from ia_assistant.models import Agent, FunctionTool, AgentWorkflow, OllamaLLM, RAGApplication, StaticMemory


@admin.register(OllamaLLM)
class OllamaLLMAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_name']


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(FunctionTool)
class FunctionToolAdmin(admin.ModelAdmin):
    list_display = ['agent_name', 'name', 'description']

    def agent_name(self, obj):
        return obj.agent.name

    agent_name.admin_order_field = 'agent'
    agent_name.short_description = 'Agente'


@admin.register(AgentWorkflow)
class AgentWorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'active']
    filter_horizontal = ['agents']


@admin.register(RAGApplication)
class RAGApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'active']


@admin.register(StaticMemory)
class StaticMemoryAdmin(admin.ModelAdmin):
    list_display = ['application', 'name', 'active']
