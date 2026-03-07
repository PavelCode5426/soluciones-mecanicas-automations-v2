from django.contrib import admin

from ia_assistant.models import Agent, AgentTool, AgentWorkflow


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(AgentTool)
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