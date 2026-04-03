from django.db import models
from django.utils.timezone import now

from core.models import WeekDay


# Create your models here.
class WhatsAppAccount(models.Model):
    name = models.CharField(max_length=250)
    chat_id = models.CharField(max_length=250)
    session = models.CharField(max_length=250)

    can_use_webhook = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Cuenta'
        verbose_name_plural = 'Cuentas'


class WhatsAppGroup(models.Model):
    account = models.ForeignKey(WhatsAppAccount, related_name='groups', on_delete=models.PROTECT)
    name = models.CharField(editable=False, max_length=250)
    chat_id = models.CharField(editable=False, max_length=250)
    is_locked = models.BooleanField(default=False, editable=False)
    is_ephemeral = models.BooleanField(default=False, editable=False)
    participant_count = models.IntegerField(editable=False)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'


class WhatsAppContact(models.Model):
    chat_id = models.CharField(editable=False, max_length=250)
    name = models.CharField(blank=True, null=True, max_length=250)
    push_name = models.CharField(editable=False, blank=True, null=True, max_length=250)
    account = models.ForeignKey(WhatsAppAccount, related_name='contacts', on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Contacto'
        verbose_name_plural = 'Contactos'


class WhatsAppStatus(models.Model):
    name = models.CharField(max_length=250)
    caption = models.TextField(blank=True)
    message_type = models.CharField(
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('video', 'Video'),
            ('audio', 'Audio'),
        ], default='text', max_length=10
    )
    file = models.FileField(upload_to='whatsapp_status', blank=True)
    account = models.ForeignKey(WhatsAppAccount, related_name='status', on_delete=models.PROTECT)

    publish_at = models.TimeField(null=True, blank=True, default=now)
    from_date = models.DateField(null=True, blank=True, default=now)
    until_date = models.DateField(null=True, blank=True)
    weekdays = models.ManyToManyField(WeekDay, related_name='whatsapp_status', blank=True)
    published_count = models.BigIntegerField(default=0)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'


class WhatsAppDistributionList(models.Model):
    name = models.CharField(max_length=250)
    account = models.ForeignKey(WhatsAppAccount, related_name='distribution_lists', on_delete=models.PROTECT)
    contacts = models.ManyToManyField(WhatsAppContact, related_name='distribution_lists', blank=True)
    groups = models.ManyToManyField(WhatsAppGroup, related_name='distribution_lists', blank=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f"{self.name} - {self.account}"

    class Meta:
        verbose_name = 'Lista de Distribución'
        verbose_name_plural = 'Listas de Distribución'


class WhatsAppMessage(models.Model):
    name = models.CharField(max_length=250)
    account = models.ForeignKey(WhatsAppAccount, related_name='messages', on_delete=models.PROTECT)
    message_type = models.CharField(
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('video', 'Video'),
            ('file', 'File'),
            ('audio', 'Audio'),
        ], default='text', max_length=10
    )

    message = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='whatsapp_messages', blank=True, null=True)

    distribution_lists = models.ManyToManyField(WhatsAppDistributionList, related_name='messages', blank=True)
    from_date = models.DateField(null=True, blank=True, default=now)
    until_date = models.DateField(null=True, blank=True)

    frequency = models.IntegerField(default=0, choices=[
        (2, "Publicar cada 2h"),
        (4, "Publicar cada 4h"),
        (8, "Publicar cada 8h"),
    ])

    publish_at = models.TimeField(null=True, blank=True)
    weekdays = models.ManyToManyField(WeekDay, related_name='whatsapp_messages', blank=True)
    published_count = models.BigIntegerField(default=0)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
