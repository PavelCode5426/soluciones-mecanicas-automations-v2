from django.contrib import admin, messages
from django.utils.timezone import now
from django_q.admin import TaskAdmin, QueueAdmin
from django_q.models import Task, OrmQ
from django_q.tasks import async_task

from facebook.models import FacebookProfile, FacebookGroup, FacebookGroupCategory, FacebookPost
from facebook.tasks import download_groups_task


# Register your models here.

@admin.register(FacebookProfile)
class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('name',)
    actions = ['sync_facebook_groups']

    def sync_facebook_groups(self, request, queryset):
        users = queryset.all()
        for user in users:
            async_task(download_groups_task, user, task_name=f"download_{user}_groups")
        self.message_user(request, "Tarea programada correctamente", level=messages.SUCCESS)

    sync_facebook_groups.short_description = 'Actualizar grupos del perfil'


@admin.register(FacebookGroup)
class FacebookGroudAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "active")


@admin.register(FacebookGroupCategory)
class FacebookGroupCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(FacebookPost)
class FacebookFacebookPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_count', 'updated_at', 'active')


admin.site.unregister(OrmQ)


class NewQueueAdmin(QueueAdmin):
    actions = QueueAdmin.actions + ('clear_queue', 'execute_now',)

    def clear_queue(self, request, query):
        self.model.delete()
        self.message_user(request, f"Todos los elementos borrados correctamente", level=messages.SUCCESS)

    clear_queue.short_description = 'Vaciar todas las tareas.'

    def execute_now(self, request, query):
        count = query.update(lock=now())
        self.message_user(request, f"{count} registros marcados como activos.", level=messages.SUCCESS)

    execute_now.short_description = 'Actualizar fecha de ejecucion de las tareas seleccionadas.'


admin.site.register(OrmQ, NewQueueAdmin)
