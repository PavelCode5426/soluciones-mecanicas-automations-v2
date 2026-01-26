from django.contrib import admin
from django_q.tasks import async_task

from facebook.models import FacebookProfile, FacebookGroup, FacebookGroupCategory, FacebookPost
from facebook.tasks import download_groups_task


# Register your models here.

@admin.action(description='Actualizar grupos del perfil')
def sync_facebook_groups(modeladmin, request, queryset):
    users = queryset.all()
    for user in users:
        async_task(download_groups_task, user, task_name=f"download_{user}_groups")


@admin.register(FacebookProfile)
class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('name',)
    actions = [sync_facebook_groups]


@admin.register(FacebookGroup)
class FacebookGroudAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "active")


@admin.register(FacebookGroupCategory)
class FacebookGroupCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(FacebookPost)
class FacebookFacebookPostAdmin(admin.ModelAdmin):
    list_display = ('title','active')
