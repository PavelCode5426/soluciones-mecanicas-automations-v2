import datetime

from dateutil.utils import today
from django.db import models
from django_jsonform.models.fields import JSONField

from core.models import WeekDay, Schedule, SoftDeleteUserTrackedModel, SoftDeleteModel
from ia_assistant.models import RAGApplication
from whatsapp.helpers import get_message_type
from whatsapp.managers import ProcessedLeadManager


class AbstractWhatsAppMessage(SoftDeleteModel):
    name = models.CharField(max_length=250)
    message_type = models.CharField(choices=[
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
        ('audio', 'Audio'),
    ], default='text', max_length=10)
    message = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

    account = models.ForeignKey('WhatsAppAccount', on_delete=models.PROTECT)
    file = models.FileField(blank=True, null=True)

    last_whatsapp_id = models.TextField(blank=True, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def save(self, *args, **kwargs):
        self.message_type = 'text' if not self.file else get_message_type(self.file)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ScheduledMessage(models.Model):
    from_date = models.DateField(null=True, blank=True, default=today)
    until_date = models.DateField(null=True, blank=True)

    weekdays = models.ManyToManyField(WeekDay, blank=True)
    published_count = models.BigIntegerField(default=0)

    class Meta:
        abstract = True


# Create your models here.
class WhatsAppAccount(SoftDeleteUserTrackedModel):
    name = models.CharField(max_length=250)
    avatar = models.ImageField(blank=True, null=True, upload_to="whatsapp_profile",
                               default="defaults/profile.jpg", editable=False)
    chat_id = models.CharField(max_length=250)
    session = models.CharField(max_length=250)

    automatic_message = models.ForeignKey('WhatsAppAutoReplyMessage', blank=True, null=True, on_delete=models.PROTECT)

    can_use_webhook = models.BooleanField(default=False)
    can_auto_reply = models.BooleanField(default=False)

    can_find_leads = models.BooleanField(default=True)
    lead_prompt = models.TextField(blank=True, null=False)

    can_reply_with_ia = models.BooleanField(default=False)
    ia_application = models.ForeignKey(RAGApplication, blank=True, null=True, on_delete=models.PROTECT)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Cuenta'
        verbose_name_plural = 'Cuentas'


class WhatsAppGroup(SoftDeleteModel):
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


class WhatsAppContact(SoftDeleteModel):
    chat_id = models.CharField(max_length=250)
    name = models.CharField(blank=True, null=True, max_length=250)
    push_name = models.CharField(blank=True, null=True, max_length=250)
    account = models.ForeignKey(WhatsAppAccount, related_name='contacts', on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Contacto'
        verbose_name_plural = 'Contactos'


class WhatsAppLead(models.Model):
    chat_id = models.CharField(editable=False, max_length=250)
    chat_name = models.CharField(editable=False, max_length=250)
    message = models.TextField(editable=False)
    media_url = models.URLField(editable=False, blank=True, null=True)
    group = models.ForeignKey(WhatsAppGroup, related_name='leads', on_delete=models.PROTECT, null=True)
    account = models.ForeignKey(WhatsAppAccount, related_name='leads', on_delete=models.PROTECT)

    message_reply = models.TextField(blank=True, null=True)
    processed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = 'Posible Cliente'
        verbose_name_plural = 'Posibles Clientes'


class WhatsAppStatus(AbstractWhatsAppMessage, ScheduledMessage):
    account = models.ForeignKey(WhatsAppAccount, related_name='status', on_delete=models.PROTECT)
    file = models.FileField(upload_to='whatsapp_status', blank=True)

    order = models.IntegerField(default=0)
    schedule = models.ForeignKey(Schedule, null=True, on_delete=models.PROTECT)
    weekdays = models.ManyToManyField(WeekDay, related_name='whatsapp_status')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['account', 'order']


class WhatsAppDistributionList(SoftDeleteModel):
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


class WhatsAppMessage(AbstractWhatsAppMessage, ScheduledMessage):
    account = models.ForeignKey(WhatsAppAccount, related_name='messages', on_delete=models.PROTECT)
    file = models.FileField(upload_to='whatsapp_messages', blank=True, null=True)

    distribution_lists = models.ManyToManyField(WhatsAppDistributionList, related_name='messages', blank=True)

    order = models.IntegerField(default=0)
    frequency = models.IntegerField(default=8, null=True, choices=[
        (None, "Sin intervalo"),
        (2, "Publicar cada 2h"),
        (4, "Publicar cada 4h"),
        (8, "Publicar cada 8h"),
    ])

    from_time = models.TimeField(default=datetime.time(0, 0))
    until_time = models.TimeField(default=datetime.time(23, 59))
    weekdays = models.ManyToManyField(WeekDay, related_name='whatsapp_messages', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        ordering = ['account', 'order']


class WhatsAppAutoReplyMessage(AbstractWhatsAppMessage):
    JSON_SCHEMA = {
        'type': 'list',
        "items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "rows": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "rowId": {"type": "string"},
                            "description": {"type": ["string", "null"]}
                        }
                    }
                }
            }
        }
    }

    trigger_message = models.CharField(max_length=250)
    message_type = models.CharField(choices=[
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
        ('audio', 'Audio'),
        ('list', 'List')
    ], default='text', max_length=10)

    account = models.ForeignKey(WhatsAppAccount, related_name='auto_replies', on_delete=models.PROTECT)
    file = models.FileField(upload_to='auto_replies', blank=True, null=True)

    title = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True, null=True)
    footer = models.TextField(blank=True, null=True)
    button_label = models.CharField(max_length=100, blank=True, null=True)
    sections = JSONField(schema=JSON_SCHEMA, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Mensaje automático"
        verbose_name_plural = "Mensajes Automáticos"


class WhatsAppProcessedLead(WhatsAppLead):
    objects = ProcessedLeadManager()

    class Meta:
        verbose_name = 'Cliente Procesado'
        verbose_name_plural = 'Clientes Procesados'
        proxy = True


class WhatsAppScheduleMessage(models.Model):
    order = models.IntegerField(default=0)
    message = models.ForeignKey(WhatsAppMessage, related_name='schedules', on_delete=models.PROTECT)
    schedule = models.ForeignKey(Schedule, related_name='messages', on_delete=models.PROTECT)
