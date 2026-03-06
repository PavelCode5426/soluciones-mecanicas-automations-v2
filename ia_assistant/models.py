from django.db import models


# Create your models here.
class Agent(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    system_prompt = models.TextField(null=True, blank=True)
