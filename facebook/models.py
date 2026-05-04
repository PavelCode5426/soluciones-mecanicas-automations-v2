from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import now

from core.models import WeekDay, SoftDeleteModel, SoftDeleteUserTrackedModel, Schedule


# Create your models here.
class FacebookFile(models.Model):
    file = models.ImageField(upload_to='facebook_files')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


class FacebookRealAccount(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    context = models.JSONField(default=dict, blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class FacebookGroup(SoftDeleteModel):
    profile = models.ForeignKey('FacebookProfile', related_name='groups', null=True, blank=True,
                                on_delete=models.SET_NULL)
    name = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    screenshot = models.ImageField(upload_to='groups_screenshots', null=True, blank=True)
    error_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"


class FacebookAccountGroup(models.Model):
    account = models.ForeignKey(FacebookRealAccount, related_name='groups', on_delete=models.CASCADE)
    group = models.ForeignKey(FacebookGroup, related_name='real_accounts', on_delete=models.CASCADE)
    pending_posts = models.IntegerField(default=0)


class FacebookProfileGroup(models.Model):
    profile = models.ForeignKey('FacebookProfile', related_name='profile_groups', on_delete=models.CASCADE)
    group = models.ForeignKey(FacebookGroup, related_name='profiles', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)


class FacebookDistributionList(SoftDeleteModel):
    profile = models.ForeignKey('FacebookProfile', related_name='distribution_lists', on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    groups = models.ManyToManyField(FacebookGroup, related_name='distribution_lists', blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.profile})"

    class Meta:
        verbose_name = "Lista de Distribución"
        verbose_name_plural = "Listas de Distribución"


class FacebookProfile(SoftDeleteUserTrackedModel):
    name = models.CharField(max_length=250)
    context = models.JSONField(default=dict, blank=True, null=True)
    active = models.BooleanField(default=True)
    can_search_leads = models.BooleanField(default=False)
    can_post_in_groups = models.BooleanField(default=True)
    posts_footer = models.TextField(null=True, blank=True)
    real_accounts = models.ManyToManyField(FacebookRealAccount, related_name='profiles', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cuentas"
        verbose_name_plural = "Cuentas"


class AbstractFacebookPost(SoftDeleteModel):
    profile = models.ForeignKey(FacebookProfile, null=True, blank=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    title = models.CharField(max_length=250, null=True, blank=True)
    text = models.TextField(blank=True, null=True)
    file = models.ImageField(upload_to='facebook_post', null=True, blank=True)
    files = GenericRelation(FacebookFile)
    hashtags = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class FacebookScheduledPost(AbstractFacebookPost):
    profile = models.ForeignKey(FacebookProfile, related_name='posts', null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"


class FacebookPostCampaign(AbstractFacebookPost):
    profile = models.ForeignKey(FacebookProfile, related_name='campaigns', null=True, blank=True,
                                on_delete=models.PROTECT)
    distribution_lists = models.ManyToManyField(FacebookDistributionList, related_name='campaigns', blank=True)
    from_date = models.DateField(default=now)
    until_date = models.DateField(null=True, blank=True)
    schedules = models.ManyToManyField(Schedule, related_name='campaigns', blank=True)

    published_count = models.BigIntegerField(default=0)
    distribution_count = models.IntegerField(default=5)

    class Meta:
        verbose_name = "Campaña"
        verbose_name_plural = "Campañas"
        ordering = ['created_at']


class FacebookAgent(SoftDeleteModel):
    name = models.CharField(max_length=250)
    profile = models.ForeignKey(FacebookProfile, related_name='agents', on_delete=models.PROTECT)
    distribution_list = models.ForeignKey(FacebookDistributionList, related_name='agents', on_delete=models.PROTECT,
                                          blank=True, null=True)
    search_keyword = models.CharField(max_length=250, null=True, blank=True)
    agent_description = models.TextField(null=True, blank=True)
    classificator_prompt = models.TextField(null=True, blank=True)
    agent_prompt = models.TextField(null=True, blank=True)

    limit = models.IntegerField(default=10)
    leads_found = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name or 'Sin nombre'

    class Meta:
        verbose_name = "Agente Comercial"
        verbose_name_plural = "Agentes Comerciales"


class FacebookHistory(SoftDeleteModel):
    profile = models.ForeignKey(FacebookProfile, related_name='histories', on_delete=models.PROTECT)
    title = models.CharField(max_length=250)
    text = models.TextField(blank=True, null=True)
    file = models.ImageField(upload_to='facebook_histories', null=True, blank=True)
    active = models.BooleanField(default=True)

    from_date = models.DateField(null=True, blank=True, default=now)
    until_date = models.DateField(null=True, blank=True)
    weekdays = models.ManyToManyField(WeekDay, related_name='facebook_histories', blank=False)
    schedule = models.ForeignKey(Schedule, null=True, on_delete=models.PROTECT)

    published_count = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = "Historia"
        verbose_name_plural = "Historias"
