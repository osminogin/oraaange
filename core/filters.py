import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django_filters import ChoiceFilter, FilterSet
from rest_framework.filters import BaseFilterBackend
from rest_framework_gis.filters import \
    DistanceToPointFilter as BaseDistanceToPointFilter


class SexFilter(FilterSet):
    """
    Filter by sex.
    """
    sex = ChoiceFilter(choices=get_user_model().Sex.choices)

    class Meta:
        model = get_user_model()
        fields = ('sex',)


class InterestsFilter(BaseFilterBackend):
    """
    Фильтр по интересам.
    """
    def filter_queryset(self, request, queryset, view):
        interests = request.query_params.getlist('interests')
        if interests:
            queryset = queryset.filter(interests__name__in=interests).distinct()
        return queryset


class BirthDateFilter(BaseFilterBackend):
    """
    Фильтр по возрасту.
    """
    age_param = 'age'
    date_param = 'birth_date'
    default_from = 18
    default_to = 28

    def filter_queryset(self, request, queryset, view):
        age = request.query_params.get(self.age_param, None)
        if not age:
            return queryset

        age_from, age_to = self.get_filter_params(age)
        date_range = {f'{self.date_param}__range': [age_from, age_to]}
        queryset = queryset.filter(**date_range)

        return queryset

    def get_filter_params(self, param):
        ages = [x.strip() for x in param.split('-')]
        if len(ages) == 1:
            age_to = self.default_to
        else:
            try:
                age_to = int(ages[0])
            except ValueError:
                age_to = self.default_to

        try:
            age_from = int(ages[-1])
        except ValueError:
            age_from = self.default_from

        age_to = self.age_to_date(age_to)
        age_from = self.age_to_date(age_from)
        return age_from, age_to

    def age_to_date(self, age):
        today = datetime.date.today()
        try:
            value = datetime.date(
                year=today.year - age,
                month=today.month,
                day=today.day
            )
        except ValueError:
            # 29 Feb
            yesterday = today - datetime.timedelta(days=1)
            value = datetime.date(
                year=yesterday.year - age,
                month=yesterday.month,
                day=yesterday.day
            )

        return value


# class DistanceToPointFilter(BaseDistanceToPointFilter):
#
#     def get_schema_fields(self, view):
#         fields = super().get_schema_fields(view)
#         filterset_fields = {
#             self.dist_param: NumberFilter(help_text='Distance to point, m'),
#             self.point_param: CharFilter(help_text='Point, "13.00,42.42"')
#         }
#
#         for name, field in filterset_fields.items():
#             fields.append(compat.coreapi.Field(
#                 name=name,
#                 required=False,
#                 location='query',
#                 schema=self.get_coreschema_field(field)
#             ))
#
#         return fields
#
#     def get_coreschema_field(self, field):
#         if isinstance(field, NumberFilter):
#             field_cls = compat.coreschema.Number
#         else:
#             field_cls = compat.coreschema.String
#         return field_cls(
#             description=six.text_type(field.extra.get('help_text', ''))
#         )


class WhoIsNearFilter(BaseDistanceToPointFilter):
    """
    Фильтр кто рядом.
    """
    dist_param = 'radius'

    def get_filter_point(self, request):
        """ Локация текущего пользователя - центр поиска. """
        point = request.user.location
        if not point:
            return None
        return point

    def dist_to_deg(self, dist, lat):
        result = super().dist_to_deg(dist, lat)
        return result * (1 - settings.DISTANCE_ERROR)

    def filter_queryset(self, request, queryset, view):
        """ 60 км. - максимум для радиуса поиска. """
        # Ислкючает текущего пользователя
        queryset = queryset.exclude(pk=request.user.pk)

        # XXX: Пока радиус не учитывается, если не указан ...
        radius_string = request.query_params.get(self.dist_param, None)
        if not radius_string:
            return queryset

        # XXX: ... а предполагается фильтр по дефолтовому радиусу
        dist_string = request.query_params.get(self.dist_param,
                                               settings.MAX_USERS_RADIUS)
        if int(dist_string) > settings.MAX_USERS_RADIUS:
            request.query_params[self.dist_param] = settings.MAX_USERS_RADIUS

        return super(WhoIsNearFilter, self).filter_queryset(request, queryset, view)
