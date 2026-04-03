from django.contrib import admin, messages
from django.db.models import Q
from django.utils.html import format_html
from django.utils.timezone import now
from django_q.tasks import async_task
from rest_framework.reverse import reverse

from whatsapp.factories import create_whatsapp_service
from whatsapp.helpers import get_message_type
from whatsapp.models import WhatsAppAccount, WhatsAppGroup, WhatsAppContact, WhatsAppDistributionList, WhatsAppStatus, \
    WhatsAppMessage
from whatsapp.tasks import syncronize_whatsapp_account_groups, syncronize_whatsapp_account_contacts, \
    publish_whatsapp_status, send_whatsapp_message


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

        syncronize_whatsapp_account_groups(obj)
        # syncronize_whatsapp_account_contacts(obj)
        # webhook_path = reverse('whatsapp:webhook', args=[obj.session])
        # service.update_session(webhook_url=request.build_absolute_uri(webhook_path))

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
    readonly_fields = ['name', 'chat_id', 'participant_count']
    list_filter = ['account']


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
class WhatsAppStatusAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'account', 'active']
    list_filter = ['account']
    readonly_fields = ['published_count', 'message_type', 'file_preview']
    actions = ['publish_status']
    filter_horizontal = ['weekdays']
    fieldsets = [
        ("Información del estado", {
            "fields": ["name", "account", 'caption', 'file', 'file_preview', 'active']
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
                task_name=f'create_whatsapp_status_{status.pk}',
                group='whatsapp_status',
                cluster='high_priority',
            )
        self.message_user(request, f'Agendados correctamente {len(statuses)} estados ', level=messages.SUCCESS)

    def file_preview(self, obj):
        message_type = obj.message_type
        if message_type == 'file':
            return "Link"
        elif message_type == 'audio':
            return format_html('<audio controls width="500" src="{}"/>'.format(obj.file.url))
        elif message_type == 'video':
            return format_html('<video controls  width="500" src="{}"></video>'.format(obj.file.url))
        elif message_type == 'image':
            return format_html('<img  width="500" src="{}" />'.format(obj.file.url))
        return '-'

    file_preview.short_description = 'Previsualizar'

    def save_model(self, request, obj, form, change):
        obj.message_type = 'text' if not obj.file else get_message_type(obj.file)
        obj.save()


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
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
        ("Planificación", {
            "fields": ["frequency", "publish_at", "from_date", "until_date", "weekdays"]
        }),
        ("Listas de distribución", {
            "fields": ["distribution_lists"]
        }),
        ("Estadísticas", {
            "fields": ["published_count"],
            "classes": ["collapse"]
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

    def file_preview(self, obj):
        message_type = obj.message_type
        if message_type == 'file':
            return "Link"
        elif message_type == 'audio':
            return format_html('<audio controls width="500" src="{}"/>'.format(obj.file.url))
        elif message_type == 'video':
            return format_html('<video controls  width="500" src="{}"></video>'.format(obj.file.url))
        elif message_type == 'image':
            return format_html('<img  width="500" src="{}" />'.format(obj.file.url))
        return '-'

    file_preview.short_description = 'Previsualizar'

    def save_model(self, request, obj, form, change):
        obj.message_type = 'text' if not obj.file else get_message_type(obj.file)
        obj.save()

    @admin.action(description='Enviar los mensajes seleccionados.')
    def send_messages(self, request, queryset):
        _messages = (queryset.filter(active=True).all())

        for message in _messages:
            # send_whatsapp_message(message)
            async_task(
                send_whatsapp_message, message,
                task_name=f'send_whatsapp_message_{message.pk}',
                group='send_whatsapp_message',
                cluster='high_priority',
            )
        self.message_user(request, f'Agendados correctamente {len(_messages)} mensajes', level=messages.SUCCESS)
