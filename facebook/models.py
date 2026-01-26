from django.db import models


# Create your models here.
class FacebookGroup(models.Model):
    name = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    screenshot = models.ImageField(upload_to='groups_screenshots', null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class FacebookGroupCategory(models.Model):
    name = models.CharField(max_length=250)
    groups = models.ManyToManyField(FacebookGroup, related_name='categories')

    def __str__(self):
        return self.name


class FacebookProfile(models.Model):
    name = models.CharField(max_length=250)
    context = models.JSONField(default=dict)
    state_file = models.FileField(upload_to='profile_states', null=True, blank=True)

    def __str__(self):
        return self.name


class FacebookPost(models.Model):
    title = models.CharField(max_length=250)
    text = models.TextField()
    file = models.ImageField(upload_to='facebook_post', null=True, blank=True)
    categories = models.ManyToManyField(FacebookGroupCategory, related_name='posts')
    active = models.BooleanField(default=True)
