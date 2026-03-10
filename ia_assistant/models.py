from django.core.cache import cache
from django.db import models
from django_jsonform.models.fields import JSONField


# Create your models here.

class OllamaLLM(models.Model):
    JSON_SCHEMA = {
        'type': 'dict',
        'keys': {
            'context_window': {'type': 'number', 'default': -1},
            'request_timeout': {'type': 'number', 'default': 120, }
        },
        'additionalProperties': True
    }

    name = models.CharField(max_length=100)
    base_url = models.CharField(max_length=100, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    config = JSONField(schema=JSON_SCHEMA)

    def __str__(self):
        return self.name


class Agent(models.Model):
    JSON_SCHEMA = {
        'type': 'dict',
        'keys': {
            'verbose': {'type': 'boolean', 'default': False},
        },
        'additionalProperties': True
    }

    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    system_prompt = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    options = JSONField(schema=JSON_SCHEMA)
    llm = models.ForeignKey(OllamaLLM, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.name


class AgentWorkflow(models.Model):
    JSON_SCHEMA = {
        'type': 'dict',
        'keys': {
            'verbose': {'type': 'boolean', 'default': False},
        },
        'additionalProperties': True
    }
    name = models.CharField(max_length=250)
    agents = models.ManyToManyField(Agent, related_name='workflows')
    root_agent = models.ForeignKey(Agent, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    options = JSONField(schema=JSON_SCHEMA)

    def __str__(self):
        return self.name


class FunctionTool(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    function = models.CharField(max_length=250)
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class RAGApplication(models.Model):
    JSON_SCHEMA = {
        'type': 'object',
        'keys': {
            'waha_base_url': {'type': 'string', 'placeholder': 'https://whatsapp.com'},
            'waha_api_key': {'type': 'string', 'placeholder': 'admin'},
            'waha_username': {'type': 'string', 'placeholder': 'admin'},
            'waha_password': {'type': 'string', 'placeholder': 'admin'},
        },
        'additionalProperties': True
    }

    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    root_agent = models.ForeignKey(Agent, on_delete=models.PROTECT, null=True, blank=True)
    root_workflow = models.ForeignKey(AgentWorkflow, on_delete=models.PROTECT, null=True, blank=True)
    active = models.BooleanField(default=True)
    config = JSONField(schema=JSON_SCHEMA)

    def save(self, *args, **kwargs):
        cache.delete(self.name)
        super().save(*args, **kwargs)
