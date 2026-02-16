from django.db import models


# Create your models here.
class FacebookGroup(models.Model):
    name = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    screenshot = models.ImageField(upload_to='groups_screenshots', null=True, blank=True)
    error_at = models.DateTimeField(null=True, blank=True)
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
    active = models.BooleanField(default=True)
    posts_footer = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class FacebookPost(models.Model):
    title = models.CharField(max_length=250)
    text = models.TextField()
    file = models.ImageField(upload_to='facebook_post', null=True, blank=True)
    categories = models.ManyToManyField(FacebookGroupCategory, related_name='posts')
    active = models.BooleanField(default=True)
    published_count = models.BigIntegerField(default=0)
    distribution_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
