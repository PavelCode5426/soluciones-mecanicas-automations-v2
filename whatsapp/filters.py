from django.db.models import Q
from django_filters import FilterSet, filters

from whatsapp import models


def _current_user_accounts(request):
    return models.WhatsAppAccount.user_objects.all()


def _current_user_distributionlists(request):
    return models.WhatsAppDistributionList.objects.filter(account__created_by=request.user, active=True)


class WhatsAppGenericFilterSet(FilterSet):
    account = filters.ModelChoiceFilter(queryset=_current_user_accounts, label="Cuentas")
    search = filters.CharFilter(method='search_method', label="Buscar...")


class WhatsAppStatusFilterSet(WhatsAppGenericFilterSet):
    def search_method(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(message__icontains=value)
        )


class WhatsAppGroupsFilterSet(WhatsAppGenericFilterSet):

    def search_method(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value))

    class Meta:
        fields = ['account', 'distributions_lists', 'search']


class WhatsAppContactsFilterSet(WhatsAppGenericFilterSet):
    distribution_lists = filters.ModelChoiceFilter(queryset=_current_user_distributionlists,
                                                   label="Listas de ditribución")

    def search_method(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(chat_id__icontains=value))

    class Meta:
        fields = ['account', 'distribution_lists', 'search']


class WhatsAppMessagesFilterSet(WhatsAppStatusFilterSet):
    pass
