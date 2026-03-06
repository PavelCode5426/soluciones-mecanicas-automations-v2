from django.contrib import admin

from ia_assistant.models import Agent

# Register your models here.
@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
