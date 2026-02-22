from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.timezone import now
from django_q.admin import QueueAdmin
from django_q.models import OrmQ
from django_q.tasks import async_task

from marketing.models import FacebookProfile, FacebookGroup, FacebookGroupCategory, FacebookPost
from marketing.tasks import download_groups_task, enqueue_posts


# Register your models here.

@admin.register(FacebookProfile)
class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('name',)
    actions = ['sync_facebook_groups']

    def sync_facebook_groups(self, request, queryset):
        users = queryset.all()
        for user in users:
            async_task(download_groups_task, user, task_name=f"download_{user}_groups".lower(), cluster='high_priority')
        self.message_user(request, "Tarea programada correctamente", level=messages.SUCCESS)

    sync_facebook_groups.short_description = 'Actualizar grupos del perfil'


@admin.register(FacebookGroup)
class FacebookGroudAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "active", "error_at",)
    readonly_fields = ("image",)

    def image(self, obj):
        return format_html('<img  width="500" src="{}" />'.format(obj.screenshot.url))

    image.short_description = 'Image'


@admin.register(FacebookGroupCategory)
class FacebookGroupCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(FacebookPost)
class FacebookFacebookPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_count', 'updated_at', 'active')
    actions = ['add_to_queue']
    readonly_fields = ["image"]

    def image(self, obj):
        return format_html('<img  width="500" src="{}" />'.format(obj.file.url))

    image.short_description = 'Image'

    def add_to_queue(self, request, query):
        user = FacebookProfile.objects.first()
        total_items = enqueue_posts(user, posts=query.all())
        self.message_user(request, f"Fueron agendadas {total_items} publicaciones", level=messages.SUCCESS)

    add_to_queue.short_description = 'Agendar publicaciones'

    def disable_posts(self, request, queryset):
        total_items = queryset.update(active=False)
        self.message_user(request, f"Fueron desactivadas {total_items} publicaciones", level=messages.SUCCESS)

    disable_posts.short_description = 'Desactivar publicaciones'

    def enable_posts(self, request, queryset):
        total_items = queryset.update(active=True)
        self.message_user(request, f"Fueron activadas {total_items} publicaciones", level=messages.SUCCESS)

    enable_posts.short_description = 'Activar publicaciones'


admin.site.unregister(OrmQ)


class NewQueueAdmin(QueueAdmin):
    actions = QueueAdmin.actions + ('clear_queue', 'execute_now',)

    def clear_queue(self, request, query):
        OrmQ.objects.all().delete()
        self.message_user(request, f"Todos los elementos borrados correctamente", level=messages.SUCCESS)

    clear_queue.short_description = 'Vaciar todas las tareas.'

    def execute_now(self, request, query):
        count = query.update(lock=now())
        self.message_user(request, f"{count} registros marcados como activos.", level=messages.SUCCESS)

    execute_now.short_description = 'Actualizar fecha de ejecucion de las tareas seleccionadas.'


admin.site.register(OrmQ, NewQueueAdmin)
