import django_filters
from django.db.models import Q
from django.utils import timezone
from django_filters.filters import CharFilter, UUIDFilter
from psycopg2.extras import NumericRange

from .models import Ad


class AdFilter(django_filters.rest_framework.FilterSet):
    user__uuid__ne = UUIDFilter(
        field_name='user__uuid', method='exclude_user'
    )
    age = CharFilter(field_name='ages', method='filter_ages')
    # XXX: BooleanFilter doesn't work as expected
    is_favorite = CharFilter(
        field_name='favorited_for', method='filter_favorite'
    )
    is_archive = CharFilter(method='filter_archive')
    is_actual = CharFilter(method='filter_actual')

    class Meta:
        model = Ad
        fields = {
            'user__uuid': ['exact'],
            'created_at': ['lt', 'gt'],
            'type': ['exact'],
            'sex': ['exact']
        }

    def exclude_user(self, queryset, name, value):
        return queryset.exclude(user__uuid=value)

    def filter_actual(self, queryset, name, value):
        """ Актуальные предложения. """
        if value in ('true', 'True', '1'):
            return queryset.filter(
                Q(period__startswith__gte=timezone.now()) |
                Q(period__endswith__gte=timezone.now())
            )
        elif value in ('false', 'False', '0'):
            return queryset.filter(
                Q(period__startswith__lt=timezone.now()) |
                Q(period__endswith__lt=timezone.now())
            )

        return queryset

    def filter_archive(self, queryset, name, value):
        """ Срок завершения предложения вышел. """
        if value in ('true', 'True', '1'):
            return queryset.filter(
                Q(period__startswith__lt=timezone.now()) |
                Q(period__endswith__lt=timezone.now())
            )

        return queryset

    def filter_favorite(self, queryset, name, value):
        if value in (True, 'True', 'true', '1'):
            value = True
        elif value in (False, 'False', 'false', '0'):
            value = False
        else:
            value = None

        if value:
            queryset = queryset.filter(
                favorited_for__contains=[self.request.user.uuid]
            )
        elif value is False:
            queryset = queryset.exclude(
                favorited_for__contains=[self.request.user.uuid]
            )

        return queryset

    def filter_ages(self, queryset, name, value):
        if not value:
            return queryset
        age_from, age_to = self._get_age_filter_params(value)
        return queryset.filter(ages__contains=NumericRange(age_from, age_to))

    def _get_age_filter_params(self, param):
        ages = [x.strip() for x in param.split('-')]
        try:
            age_from = int(ages[0])
        except (ValueError, IndexError):
            age_from = None

        try:
            age_to = int(ages[1])
        except (ValueError, IndexError):
            age_to = None

        return age_from, age_to
