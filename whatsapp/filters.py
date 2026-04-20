from django.db.models import Q
from django_filters import FilterSet, filters

from whatsapp import models


class WhatsAppGenericFilterSet(FilterSet):
    account = filters.ModelChoiceFilter(queryset=models.WhatsAppAccount.objects.all(), label="Cuentas")
    search = filters.CharFilter(method='search_method', label="Buscar...")


class WhatsAppStatusFilterSet(WhatsAppGenericFilterSet):
    def search_method(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(message__icontains=value)
        )


class WhatsAppGroupsFilterSet(WhatsAppGenericFilterSet):

    def search_method(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
        )

    class Meta:
        fields = ['account', 'distributions_lists', 'search']


class WhatsAppContactsFilterSet(WhatsAppGenericFilterSet):
    distribution_lists = filters.ModelChoiceFilter(
        queryset=models.WhatsAppDistributionList.objects.filter(active=True), label="Listas de ditribución")

    def search_method(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(chat_id__icontains=value)
        )

    class Meta:
        fields = ['account', 'distribution_lists', 'search']


class WhatsAppMessagesFilterSet(WhatsAppStatusFilterSet):
    pass
