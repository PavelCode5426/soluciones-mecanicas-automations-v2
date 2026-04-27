from django.db.models import Q
from django_filters import FilterSet, filters

from facebook import models


class FacebookGenericFilterSet(FilterSet):
    profile = filters.ModelChoiceFilter(queryset=models.FacebookProfile.objects.all(), label="Cuentas")
    search = filters.CharFilter(method='search_method', label="Buscar...")


class FacebookGroupsFilterSet(FacebookGenericFilterSet):

    def search_method(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value))

    class Meta:
        fields = ['profile', 'search']


class FacebookPostCampaingFilterSet(FacebookGenericFilterSet):

    def search_method(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value))

    class Meta:
        fields = ['account', 'search']
