from django.contrib import admin

from core.models import WeekDay, Schedule


# Register your models here.

class ClientAdminSite(admin.AdminSite):
    site_header = "Panel para Clientes"
    site_title = "Portal de Clientes"
    index_title = "Bienvenido al panel de clientes"

    def has_permission(self, request):
        return request.user.is_authenticated and not request.user.is_staff


client_admin = ClientAdminSite(name='admin')


@admin.register(WeekDay)
class WeekDayAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['name']
