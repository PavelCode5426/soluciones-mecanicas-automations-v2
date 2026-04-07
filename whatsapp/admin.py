from django.contrib import admin, messages
from django.core.cache import cache
from django.db.models import Q
from django.utils.html import format_html
from django.utils.timezone import now
from django_q.tasks import async_task
from rest_framework.reverse import reverse

from whatsapp.factories import create_whatsapp_service
from whatsapp.helpers import get_message_type
from whatsapp.models import WhatsAppAccount, WhatsAppGroup, WhatsAppContact, WhatsAppDistributionList, WhatsAppStatus, \
    WhatsAppMessage, WhatsAppLead, WhatsAppAutoReplyMessage, WhatsAppProcessedLead
from whatsapp.tasks import syncronize_whatsapp_account_groups, syncronize_whatsapp_account_contacts, \
    publish_whatsapp_status, enqueue_whatsapp_message, enqueue_create_message_for_lead


class PreviewFileMixin:
    def file_preview(self, obj):
        message_type = obj.message_type
        if message_type == 'file':
            return "Fichero de documento"
        elif message_type == 'audio':
            return format_html('<audio controls width="500" src="{}"/>'.format(obj.file.url))
        elif message_type == 'video':
            return format_html('<video controls  width="500" src="{}"></video>'.format(obj.file.url))
        elif message_type == 'image':
            return format_html('<img  width="500" src="{}" />'.format(obj.file.url))
        return '-'

    file_preview.short_description = "Previsualizar"


# Register your models here.
@admin.register(WhatsAppAccount)
class WhatsAppAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'session', 'active']
    readonly_fields = ['name', 'session', 'chat_id']
    actions = ['sync_whatsapp_groups', 'sync_whatsapp_contacts']

    def get_readonly_fields(self, request, obj=None):
        fields = [*super().get_readonly_fields(request, obj)]
        if not obj:
            fields.remove('session')
        return fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and not obj.can_reply_with_ia:
            fields.remove('agent_prompt')
        if obj and not obj.can_find_leads:
            fields.remove('lead_prompt')
        return fields

    def save_model(self, request, obj, form, change):
        service = create_whatsapp_service(obj)
        # is_new_account = obj.pk is None
        # if is_new_account:
        #     service.create_session()

        obj.save()
        profile = service.get_profile_info()
        obj.name = profile['name']
        obj.chat_id = profile['id']
        obj.save()
        cache.delete(obj.session)

        syncronize_whatsapp_account_groups(obj)
        # syncronize_whatsapp_account_contacts(obj)
        webhooks_urls = []
        if obj.can_auto_reply:
            webhooks_urls.append(request.build_absolute_uri(reverse('whatsapp:chats-webhook')))
        if obj.can_find_leads:
            webhooks_urls.append(request.build_absolute_uri(reverse('whatsapp:groups-webhook')))
        service.update_session(webhooks_urls)

    @admin.action(description='Actualizar grupos de la cuenta')
    def sync_whatsapp_groups(self, request, queryset):
        accounts = queryset.all()
        for account in accounts:
            syncronize_whatsapp_account_groups(account)
        self.message_user(request, "Grupos actualizados correctamente", level=messages.SUCCESS)

    @admin.action(description='Actualizar contactos de la cuenta')
    def sync_whatsapp_contacts(self, request, queryset):
        accounts = queryset.all()
        for account in accounts:
            syncronize_whatsapp_account_contacts(account)
        self.message_user(request, "Contactos actualizados correctamente", level=messages.SUCCESS)


@admin.register(WhatsAppGroup)
class WhatsAppGroupAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'account', 'participant_count', 'active']
    readonly_fields = ['name', 'chat_id', 'participant_count', 'is_locked', 'is_ephemeral']
    list_filter = ['account']


@admin.register(WhatsAppLead)
class WhatsAppLeadAdmin(admin.ModelAdmin):
    list_display = ['chat_name', 'chat_id', 'group', 'created_at']
    readonly_fields = ['chat_id', 'chat_name', 'message', 'media_url', 'processed']
    list_filter = ['account', 'processed']
    actions = ['create_message_for_lead']

    def save_model(self, request, obj, form, change):
        obj.save()

    def delete_queryset(self, request, queryset):
        chat_ids = queryset.values_list('chat_id', flat=True).distinct()
        self.model.objects.filter(chat_id__in=chat_ids, processed=False).delete()

    @admin.action(description='Enviar propuesta al cliente')
    def create_message_for_lead(self, request, queryset):
        leads = queryset.filter(processed=False).all()
        enqueue_create_message_for_lead(leads)
        self.message_user(request, f'Se agendaron mensajes para los clientes seleccionados.', level=messages.SUCCESS)


@admin.register(WhatsAppProcessedLead)
class WhatsAppLeadAdmin(admin.ModelAdmin):
    list_display = ['chat_name', 'chat_id', 'group', 'created_at']
    readonly_fields = ['chat_id', 'chat_name', 'message', 'media_url', 'processed']
    list_filter = ['account']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(processed=True)


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    search_fields = ['name', 'chat_id']
    list_display = ['name', 'account', 'active']
    readonly_fields = ['chat_id']
    list_filter = ['account']


@admin.register(WhatsAppDistributionList)
class WhatsAppDistributionListAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'account', 'active']
    list_filter = ['account']
    filter_horizontal = ['groups', 'contacts']
    readonly_fields = ['account']

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj else []

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj is None:
            fields.remove('groups')
            fields.remove('contacts')
        return fields

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.pk:
            form.base_fields['groups'].queryset = WhatsAppGroup.objects.filter(account=obj.account).all()
            form.base_fields['contacts'].queryset = WhatsAppContact.objects.filter(account=obj.account).all()
        return form


@admin.register(WhatsAppStatus)
class WhatsAppStatusAdmin(admin.ModelAdmin, PreviewFileMixin):
    search_fields = ['name']
    list_display = ['name', 'account', 'active']
    list_filter = ['account']
    readonly_fields = ['published_count', 'message_type', 'file_preview']
    actions = ['publish_status']
    filter_horizontal = ['weekdays']
    fieldsets = [
        ("Información del estado", {
            "fields": ["name", "account", 'message', 'file', 'file_preview', 'active']
        }),
        ("Planificar estado", {
            "fields": ['published_count', 'publish_at', 'from_date', 'until_date', 'weekdays']
        }),
    ]

    @admin.action(description='Publicar los estados seleccionados.')
    def publish_status(self, request, queryset):
        statuses = (queryset.filter(active=True, from_date__lte=now())
                    .filter(Q(until_date__gte=now()) | Q(until_date__isnull=True))
                    .all())

        for status in statuses:
            async_task(
                publish_whatsapp_status, status,
                task_name=f'create_whatsapp_status_{status.pk}', group='whatsapp_status', cluster='high_priority',
            )
        self.message_user(request, f'Agendados correctamente {len(statuses)} estados ', level=messages.SUCCESS)

    def save_model(self, request, obj, form, change):
        obj.message_type = 'text' if not obj.file else get_message_type(obj.file)
        obj.save()


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin, PreviewFileMixin):
    search_fields = ['name', 'message']
    list_display = ['name', 'account', 'message_type', 'active', 'published_count']
    list_filter = ['account', 'active', 'message_type']
    readonly_fields = ['published_count', 'file_preview']
    filter_horizontal = ['weekdays', 'distribution_lists']
    actions = ['activar_mensajes', 'desactivar_mensajes', 'send_messages']

    fieldsets = [
        ("Información del mensaje", {
            "fields": ["name", "account", "active"]
        }),
        ("Contenido", {
            "fields": ["message", "file", "file_preview"]
        }),
        ("Listas de distribución", {
            "fields": ["distribution_lists"]
        }),
        ("Planificación", {
            "fields": ["frequency", "from_date", "until_date", "weekdays"],
            'classes': ('collapse',),
        }),
        ("Estadísticas", {
            "fields": ["published_count"],
            'classes': ('collapse',),
        }),
    ]

    @admin.action(description='Activar mensajes los seleccionados.')
    def activar_mensajes(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} mensaje(s) activado(s).')

    @admin.action(description='Desactivar mensajes los seleccionados.')
    def desactivar_mensajes(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} mensaje(s) desactivado(s).')

    def save_model(self, request, obj, form, change):
        obj.message_type = 'text' if not obj.file else get_message_type(obj.file)
        obj.save()

    @admin.action(description='Enviar los mensajes seleccionados.')
    def send_messages(self, request, queryset):
        _messages = (queryset.filter(active=True).all())

        for message in _messages:
            enqueue_whatsapp_message(message)
        self.message_user(request, f'Agendados correctamente {len(_messages)} mensajes', level=messages.SUCCESS)


@admin.register(WhatsAppAutoReplyMessage)
class WhatsAppAutoReplyMessageAdmin(admin.ModelAdmin, PreviewFileMixin):
    list_display = ['name', 'trigger_message', 'message_type', 'account', 'active', 'created_at']
    list_filter = ['message_type', 'active', 'account']
    search_fields = ['name', 'trigger_message', 'message']
    readonly_fields = ['created_at', 'updated_at', 'file_preview']
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'account', 'message_type', 'trigger_message', 'active')
        }),
        ('Contenido del Mensaje', {
            'fields': ('message', 'file', 'file_preview'),
            'classes': ('collapse',),
            'description': 'Para mensajes de tipo texto'
        }),
        ('Configuración para Listas', {
            'fields': ('title', 'description', 'footer', 'button_label', 'sections'),
            'classes': ('collapse',),
            'description': 'Estos campos solo se utilizan cuando el mensaje es tipo lista'
        })
    )

    def save_model(self, request, obj, form, change):
        """Validación adicional antes de guardar"""
        if obj.message_type == 'list':
            if not obj.sections:
                form.add_error('sections', 'El campo sections es requerido para mensajes de tipo lista')
            if not obj.button_label:
                form.add_error('button_label', 'El campo button_label es requerido para mensajes de tipo lista')
        elif obj.message_type != 'text':
            if not obj.file:
                form.add_error('file', f'El archivo es requerido para mensajes de tipo {obj.message_type}')
        elif obj.message_type == 'text':
            if not obj.message:
                form.add_error('message', 'El campo message es requerido para mensajes de tipo texto')

        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        form.base_fields[
            'sections'].help_text = 'Estructura JSON para las secciones y filas de la lista. Ver schema para formato correcto.'
        form.base_fields['button_label'].help_text = 'Texto que aparecerá en el botón de la lista'
        form.base_fields['title'].help_text = 'Título principal de la lista'
        form.base_fields['description'].help_text = 'Descripción de la lista (opcional)'
        form.base_fields['footer'].help_text = 'Texto que aparece al pie de la lista (opcional)'

        return form
