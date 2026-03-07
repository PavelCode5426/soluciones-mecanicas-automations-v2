from django.db import models


# Create your models here.
class Agent(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    system_prompt = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    options = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name


class AgentTool(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    function = models.CharField(max_length=250)
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)


class AgentWorkflow(models.Model):
    name = models.CharField(max_length=250)
    agents = models.ManyToManyField(Agent, related_name='workflows')
    root_agent = models.ForeignKey(Agent, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
