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


class AllObjectsModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = getattr(self.model, 'all_objects', self.model._default_manager).get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
