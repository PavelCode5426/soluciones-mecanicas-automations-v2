from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.timezone import now, timedelta
from django_q.admin import QueueAdmin
from django_q.models import OrmQ
from django_q.tasks import async_task

from facebook.models import FacebookProfile, FacebookGroup, FacebookDistributionList, FacebookPostCampaign, \
    FacebookAgent, \
    FacebookHistory, FacebookScheduledPost, FacebookRealAccount, FacebookProfileGroup, FacebookAccountGroup
from facebook.tasks import syncronize_account_groups, enqueue_facebook_campaign, enqueue_lead_explorer

admin.site.site_header = "Panel de Administración"
admin.site.site_title = "Sinergia Marketing Automations"
admin.site.index_title = "Bienvenido al Panel"


class PreviewFileMixin:
    def file_preview(self, obj):
        return format_html('<img  width="500" src="{}" />'.format(obj.file.url))

    file_preview.short_description = "Previsualizar"


@admin.register(FacebookRealAccount)
class FacebookRealAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'active']


@admin.register(FacebookAccountGroup)
class FacebookAccountGroupAdmin(admin.ModelAdmin):
    list_display = ['account', 'group', 'pending_posts']


@admin.register(FacebookProfileGroup)
class FacebookProfileGroupAdmin(admin.ModelAdmin):
    list_display = ['profile', 'group', 'active']


@admin.register(FacebookProfile)
class FacebookProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'active', 'can_search_leads', 'can_post_in_groups']
    actions = ['sync_facebook_groups']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        real_accounts = obj.real_accounts.filter(active=True).all()
        groups = FacebookGroup.objects.filter(real_accounts__account__in=real_accounts).distinct()
        for group in groups:
            FacebookProfileGroup.objects.update_or_create(
                create_defaults={'group': group, 'profile': obj},
                group=group, profile=obj
            )

    @admin.action(description='Actualizar grupos de las cuentas seleccionadas')
    def sync_facebook_groups(self, request, queryset):
        real_accounts = FacebookRealAccount.objects.filter(
            profiles__in=queryset.filter(active=True).all(), active=True
        ).distinct()

        for account in real_accounts:
            async_task(syncronize_account_groups, account, task_name="syncronize_account_groups",
                       cluster='high_priority')
        self.message_user(request, "Tarea programada correctamente", level=messages.SUCCESS)


@admin.register(FacebookGroup)
class FacebookGroudAdmin(admin.ModelAdmin):
    list_display = ["name", "url", "active", "error_at"]
    readonly_fields = ["image"]

    def image(self, obj):
        return format_html('<img  width="500" src="{}" />'.format(obj.screenshot.url))

    image.short_description = 'Image'


@admin.register(FacebookDistributionList)
class FacebookGroupCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'profile', 'total_groups']
    list_filter = ["profile"]
    filter_horizontal = ['groups']

    def total_groups(self, obj):
        return obj.groups.count()

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj is None:
            fields.remove('groups')
        return fields

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups":
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    category = FacebookDistributionList.objects.get(pk=obj_id)
                    kwargs["queryset"] = FacebookGroup.objects.filter(profile=category.profile)
                except FacebookDistributionList.DoesNotExist:
                    pass
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class FacebookPostAdmin(PreviewFileMixin, admin.ModelAdmin):
    search_fields = ['name', 'text']
    list_filter = ["profile"]
    actions = ['disable_posts', 'enable_posts']
    readonly_fields = ["file_preview", "created_at", "updated_at"]

    @admin.action(description='Desactivar publicaciones seleccionadas')
    def disable_posts(self, request, queryset):
        total_items = queryset.update(active=False)
        self.message_user(request, f"Fueron desactivadas {total_items} publicaciones", level=messages.SUCCESS)

    @admin.action(description='Activar publicaciones seleccionadas')
    def enable_posts(self, request, queryset):
        total_items = queryset.update(active=True)
        self.message_user(request, f"Fueron activadas {total_items} publicaciones", level=messages.SUCCESS)


@admin.register(FacebookPostCampaign)
class FacebookFacebookPostCampaignAdmin(FacebookPostAdmin):
    list_display = ['name', 'profile', 'updated_at', 'active']
    readonly_fields = FacebookPostAdmin.readonly_fields + ["published_count"]
    actions = ['add_to_queue'] + FacebookPostAdmin.actions

    filter_horizontal = ['distribution_lists']
    fieldsets = [
        ("Detalles de la publicación", {
            "fields": ["name", "profile", 'title', 'text', 'hashtags', 'file', 'file_preview', "distribution_lists"]
        }),
        ("Panificador de la publicación", {
            "fields": ['active', 'from_date', 'until_date', 'distribution_count', 'schedules']
        }),
        ("Indicadores de la publicación", {
            "fields": ['published_count', "created_at", "updated_at"]
        })
    ]

    @admin.action(description='Agendar publicaciones los seleccionadas.')
    def add_to_queue(self, request, query):
        total_items = enqueue_facebook_campaign(query.all())
        self.message_user(request, f"Fueron agendadas {total_items} publicaciones", level=messages.SUCCESS)


@admin.register(FacebookScheduledPost)
class FacebookFacebookScheduledPostAdmin(FacebookPostAdmin):
    list_display = ['name', 'profile', 'updated_at', 'active']
    fieldsets = [
        ("Detalles de la publicación", {
            "fields": ["name", "profile", 'title', 'text', 'hashtags', 'file', 'file_preview']
        }),
        ("Panificador de la publicación", {
            "fields": ['active']
        }),
    ]


@admin.register(FacebookAgent)
class FacebookLeadExplorerAdmin(admin.ModelAdmin):
    list_display = ['profile', 'distribution_list']
    list_filter = ["profile"]
    actions = ['add_to_queue']

    def add_to_queue(self, request, query):
        active_leads = query.filter(active=True).all()
        for explorer in active_leads:
            enqueue_lead_explorer(explorer)
        self.message_user(request, f"Fueron agendadas {active_leads.count()}  publicaciones", level=messages.SUCCESS)

    add_to_queue.short_description = 'Comenzar a explorar'


@admin.register(FacebookHistory)
class FacebookHistoryAdmin(PreviewFileMixin, admin.ModelAdmin):
    list_display = ["title", "profile", "active"]
    list_filter = ["profile"]
    filter_horizontal = ['weekdays']
    readonly_fields = ["created_at", "updated_at", "published_count", "file_preview"]
    fieldsets = [
        ("Detalles de la historia", {
            "fields": ['profile', 'title', 'file', 'file_preview']
        }),
        ("Estados de la historia", {
            "fields": ['active', 'from_date', 'until_date', 'schedule', 'weekdays']
        }),
        ("Indicadores de la historia", {
            "fields": ['published_count', "created_at", "updated_at"]
        })
    ]


class NewQueueAdmin(QueueAdmin):
    actions = QueueAdmin.actions + ('clear_queue', 'execute_now',)

    def clear_queue(self, request, query):
        OrmQ.objects.all().delete()
        self.message_user(request, f"Todos los elementos borrados correctamente", level=messages.SUCCESS)

    clear_queue.short_description = 'Vaciar todas las tareas.'

    def execute_now(self, request, query):
        count = query.update(lock=now() + timedelta(minutes=1))
        self.message_user(request, f"{count} registros marcados como activos.", level=messages.SUCCESS)

    execute_now.short_description = 'Actualizar fecha de ejecucion de las tareas seleccionadas.'


admin.site.unregister(OrmQ)
admin.site.register(OrmQ, NewQueueAdmin)
