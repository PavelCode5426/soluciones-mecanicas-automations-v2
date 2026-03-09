from django.contrib import admin

from ia_assistant.models import Agent, FunctionTool, AgentWorkflow, OllamaLLM


@admin.register(OllamaLLM)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_name']


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(FunctionTool)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['agent_name', 'name', 'description']

    def agent_name(self, obj):
        return obj.agent.name

    agent_name.admin_order_field = 'agent'
    agent_name.short_description = 'Agente'


@admin.register(AgentWorkflow)
class AgentWorkflow(admin.ModelAdmin):
    list_display = ['name', 'active']
    filter_horizontal = ['agents']
