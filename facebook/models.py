from django.db import models
from django.utils.timezone import now


# Create your models here.
class FacebookGroup(models.Model):
    profile = models.ForeignKey('FacebookProfile', related_name='groups', null=True, blank=True,
                                on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    screenshot = models.ImageField(upload_to='groups_screenshots', null=True, blank=True)
    error_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class FacebookGroupCategory(models.Model):
    profile = models.ForeignKey('FacebookProfile', related_name='group_categories', null=True, blank=True,
                                on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    groups = models.ManyToManyField(FacebookGroup, related_name='categories', blank=True)

    def __str__(self):
        return f"{self.name} ({self.profile})"


class FacebookProfile(models.Model):
    name = models.CharField(max_length=250)
    context = models.JSONField(default=dict)
    active = models.BooleanField(default=True)
    posts_footer = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class FacebookPost(models.Model):
    profile = models.ForeignKey(FacebookProfile, related_name='posts', null=True, blank=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    title = models.CharField(max_length=250, null=True, blank=True)
    text = models.TextField()
    file = models.ImageField(upload_to='facebook_post', null=True, blank=True)
    hashtags = models.TextField(null=True, blank=True)
    categories = models.ManyToManyField(FacebookGroupCategory, related_name='posts')
    active = models.BooleanField(default=True)
    from_date = models.DateField(null=True, blank=True, default=now)
    until_date = models.DateField(null=True, blank=True)

    published_count = models.BigIntegerField(default=0)
    distribution_count = models.IntegerField(default=0)
    frequency = models.IntegerField(default=0, choices=[
        (2, "Publicar cada 2h"),
        (4, "Publicar cada 4h"),
        (8, "Publicar cada 8h"),
    ])

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)


class FacebookLeadExplorer(models.Model):
    description = models.TextField(null=True, blank=True)
    profile = models.ForeignKey(FacebookProfile, related_name='lead_explorers', on_delete=models.PROTECT)
    group_category = models.ForeignKey(FacebookGroupCategory, related_name='lead_explorers', on_delete=models.PROTECT)
    limit = models.IntegerField(default=100)
    leads_found = models.IntegerField(default=0)
    active = models.BooleanField(default=True)


class FacebookHistory(models.Model):
    profile = models.ForeignKey(FacebookProfile, related_name='histories', on_delete=models.PROTECT)
    title = models.CharField(max_length=250)
    text = models.TextField(blank=True, null=True)
    file = models.ImageField(upload_to='facebook_histories', null=True, blank=True)
    active = models.BooleanField(default=True)

    from_date = models.DateField(null=True, blank=True, default=now)
    until_date = models.DateField(null=True, blank=True)
    published_count = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
