import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection, transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.views import FilterMixin
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from rest_framework.views import Response, status
from rest_framework_gis.filters import InBBoxFilter
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings as jwt_settings
from rest_framework_jwt.views import JSONWebTokenAPIView

from abuses.serializers import UserAbuseSerializer
from contacts.models import Contact
from core.filters import (BirthDateFilter, SexFilter,  # InterestsFilter
                          WhoIsNearFilter)
from core.permissions import OnlyOwnerAllowedEdit
from core.serializers import EmptySerializer, TokenSerializer
from core.utils import (fix_rawsql_helper, get_best_minpoints_dbscan,
                        get_meter_per_pixel, get_rows_from_cursor)
# from files.serializers import FileSerializer
from files.models import File

from .models import SMSCode
from .serializers import (ImOnlineSerializer, InitialSerializer,
                          SimpeUserSerializer, UserLocationSerializer,
                          UserSerializer, WhoIsNearListQueryParamsSerializer,
                          WhoIsNearMapQueryParamsSerializer)
from .tasks import send_sms_code

logger = logging.getLogger(__name__)


class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  FilterMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    retrive:
        Return current authorized user instance.
    update:
        Return updated current user instance.
    """
    lookup_field = 'uuid'
    queryset = get_user_model().objects.filter(is_active=True)
    permission_classes = (IsAuthenticated, OnlyOwnerAllowedEdit,)
    serializer_class = UserSerializer
    distance_filter_field = 'location'
    distance_filter_convert_meters = True
    bbox_filter_field = 'location'
    bbox_filter_include_overlapping = True  # Optional
    http_method_names = ('get', 'post', 'head', 'patch', 'delete',)

    def annotate_queryset(self, qs):
        # XXX: Лучше делать после фильтрации или после получения страницы.
        is_contact = Contact.objects.filter(
            user=OuterRef('pk'), holder=self.request.user
        )
        is_favorite = Contact.objects.filter(
            user=OuterRef('pk'), is_favorite=True, holder=self.request.user
        )
        is_blocked = self.request.user.black_list.filter(pk=OuterRef('pk'))

        qs = qs.annotate(
            is_contact=Exists(is_contact),
            is_favorite=Exists(is_favorite),
            is_blocked=Exists(is_blocked),
        )
        return qs

    def get_queryset(self):
        qs = super().get_queryset()
        return self.annotate_queryset(qs)

    def perfom_update(self, serializer):
        super().perfom_update(serializer)
        serializer.instance.files.filter(
            file_type=File.Type.AVATAR
        ).exclude(
            uuid=serializer.instance.avatar_uuid
        ).update(deleted_at=timezone.now())

    def get_kmeans_sql(self, zoom):
        """ RawSQL-реализация алгоритма K-means. """
        queryset = self.filter_queryset(self.get_queryset())
        # Тюним под зум
        if zoom < 8:
            minpoints = 2
        elif zoom <= 11:
            minpoints = 3
        else:
            minpoints = 1

        # В K-means не может быть minpoint больше самих точек
        # points_count = queryset.count()
        # if minpoints > points_count:
        #     minpoints = points_count

        users_rawquery = str(queryset.query).rstrip(';')
        sql = f"""
        WITH
            user_list as ({users_rawquery}),
            clusters as (
                SELECT
                    ST_ClusterKMeans(location, {minpoints}) OVER() AS cluster_id,
                    uuid, location, display_name, avatar_uuid
                FROM user_list
            )
        SELECT
            cluster_id, uuid, display_name, location, avatar_uuid,
            False as is_cluster
        FROM clusters WHERE cluster_id = 0

        UNION   -- Объединение
        SELECT
            cluster_id,
            '00000000-0000-0000-0000-000000000000' as uuid,
            CONCAT('Cluster ', cluster_id) as display_name,
            ST_Centroid(ST_Collect(clusters.location)) as location,
            NULL as avatar_uuid,
            True as is_cluster
        FROM clusters
        GROUP BY cluster_id
        HAVING cluster_id > 0
        """
        return fix_rawsql_helper(sql)

    def get_dbscan_sql(self, zoom, points_count, eps=50, minpoints=None):
        """ RawSQL-реализация алгоритма DBSCAN.

        Возвращает RawSQL запрос с кластеризацией точек и
        объединием со списком координат индивидуальных пользователей.
        """
        minpoints = get_best_minpoints_dbscan(points_count, minpoints)
        queryset = self.filter_queryset(self.get_queryset())
        users_rawquery = str(queryset.query).rstrip(';')
        # SRID 2956 4326
        sql = f"""
            WITH
                user_list as ({users_rawquery}),
                clusters as (
                    SELECT
                        ST_ClusterDBSCAN(ST_Transform(location, 4326), {eps}, {minpoints}) OVER() AS cluster_id,
                        uuid, location, display_name, avatar_uuid
                    FROM user_list
                )
            SELECT
                cluster_id, uuid, display_name, location, avatar_uuid,
                '1' as geom_count,
                False as is_cluster
            FROM clusters WHERE cluster_id IS NULL

            UNION   -- Объединение
            SELECT
                cluster_id,
                '00000000-0000-0000-0000-000000000000' as uuid,
                CONCAT('Cluster ', cluster_id) as display_name,
                ST_Centroid(ST_Collect(clusters.location)) as location,
                NULL as avatar_uuid,
                COUNT(clusters.location) as geom_count,
                True as is_cluster
            FROM clusters
            GROUP BY cluster_id
            HAVING cluster_id >= 0
        """
        return fix_rawsql_helper(sql)

    @swagger_auto_schema(auto_schema=None)
    def list(self, request, *args, **kwargs):
        """  Returns '405 Method Not Allowed'. """
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        methods=['get'], detail=False, serializer_class=UserLocationSerializer,
        filterset_class=SexFilter, pagination_class=None, filter_backends=(
            WhoIsNearFilter, BirthDateFilter, DjangoFilterBackend,
        )
    )
    @swagger_auto_schema(query_serializer=WhoIsNearMapQueryParamsSerializer,
                         responses={200: ''})
    def who(self, request, *args, **kwargs):
        """
        Кто рядом (карта).
        """
        query_serializer = WhoIsNearMapQueryParamsSerializer(data=request.GET)
        query_serializer.is_valid(raise_exception=True)
        zoom = query_serializer.validated_data['zoom']
        # px = query_serializer.validated_data.get('horizonta_px', 1080)
        # clusters_number = query_serializer.validated_data['clusters_number']

        queryset = self.get_queryset().filter(show_activity=True, is_online=True)
        queryset = self.filter_queryset(queryset)
        points_count = queryset.count()
        meter_pixel = get_meter_per_pixel(zoom)
        # При определенном зуме кластеризация не применяется
        if zoom >= 19.5 or points_count < 3:
            serializer = self.get_serializer(queryset, many=True)

        else:
            # Запрос сырого SQL через курсор
            with connection.cursor() as cursor:
                sql = self.get_dbscan_sql(
                    zoom=zoom, points_count=points_count,
                    eps=query_serializer.validated_data.get('eps', meter_pixel * 11),
                    minpoints=query_serializer.validated_data.get('minpoints')
                )
                cursor.execute(sql)
                # cursor.execute(self.get_kmeans_sql(zoom))
                data = get_rows_from_cursor(cursor)
                for row in data:
                    row['location'] = GEOSGeometry(row['location'])

                serializer = self.get_serializer(data, many=True)

        return Response(serializer.data)

    @action(
        methods=['get'], detail=False, serializer_class=UserLocationSerializer,
        url_path=r'who_list', url_name='who-list',
        pagination_class=GeoJsonPagination,
        filterset_class=SexFilter, filter_backends=(
            WhoIsNearFilter, BirthDateFilter, DjangoFilterBackend, InBBoxFilter,
        )
    )
    @swagger_auto_schema(query_serializer=WhoIsNearListQueryParamsSerializer,
                         responses={200: ''})
    def who_list(self, request, *args, **kwargs):
        """
        Пользователи 'Кто рядом' (список с пагинацией).
        """
        WhoIsNearListQueryParamsSerializer(data=request.GET) \
            .is_valid(raise_exception=True)

        # Only online users show
        queryset = self.get_queryset().filter(show_activity=True, is_online=True)
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        methods=['post'], detail=True, serializer_class=UserAbuseSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def abuse(self, request, uuid=None):
        user = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, sender=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(method='post', responses={201: 'Block added'})
    @swagger_auto_schema(method='delete', responses={204: 'Block removed'})
    @action(methods=['post', 'delete'], detail=True,
            permission_classes=(IsAuthenticated,),  # Remove object owner check
            serializer_class=EmptySerializer)
    def block(self, request, uuid=None):
        """ Устанавливает или снимает пользовательскую блокировку. """
        if request.method.lower() == 'post':
            request.user.black_list.add(self.get_object())
            return Response(status=status.HTTP_201_CREATED)
        elif request.method.lower() == 'delete':
            request.user.black_list.remove(self.get_object())
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False, serializer_class=SimpeUserSerializer)
    def black_list(self, request):
        """ Черный список текущего пользователя. """
        queryset = self.filter_queryset(request.user.black_list.all())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, serializer_class=ImOnlineSerializer)
    def im_online(self, request, uuid=None):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(last_ativity=datetime.now())
        return Response(serializer.data, status=status.HTTP_200_OK)

    # @action(methods=['get'], detail=True, serializer_class=FileSerializer)
    # @swagger_auto_schema(responses={200: ''})
    # def portfolio(self, request, uuid=None):
    #     # TODO: Write tests!!1
    #     instance = self.get_object()
    #     portfolio_images = instance.files.filter(file_type=File.Type.PORTFOLIO) \
    #         .order_by('-id')
    #     serializer = self.get_serializer(portfolio_images, many=True)
    #     return Response(serializer.data)


class ObtainJSONWebToken(JSONWebTokenAPIView):
    """
    Returns a JSON Web Token that can be used for authenticated requests.
    """
    serializer_class = JSONWebTokenSerializer

    @swagger_auto_schema(responses={200: TokenSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        jwt_response_payload_handler = jwt_settings.JWT_RESPONSE_PAYLOAD_HANDLER

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            user.last_login = datetime.utcnow()
            if serializer.validated_data.get('device_id'):
                user.device_id = serializer.validated_data['device_id']
            user.save()
            token = serializer.object.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response(response_data)
            if jwt_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              jwt_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InitialViewSet(mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    """
    create:
        Первая стадия авторизации - отправка на номер телефона СМС-кода.
    """
    queryset = get_user_model().objects.none()
    permission_classes = (permissions.AllowAny,)
    serializer_class = InitialSerializer

    @swagger_auto_schema(
        request_body=InitialSerializer, responses={201: ''}
    )
    def create(self, request, *args, **kwargs):
        if not isinstance(request.data, dict):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Атомарная транзакция - если что откатываем
        with transaction.atomic():
            customer = serializer.create(serializer.validated_data)

            # Уставливаем СМС-код для пользователя
            customer.sms_code = SMSCode.objects.create()
            customer.save()

            # TODO: Добавить Thorottle для однообразных запросов - эконовом смс

            # Повторная отправка СМС-кода возможна не ранее, чем через 30 сек.
            # с предыдущего запроса (и предыдущей отправки).
            if getattr(customer, 'sms_code', None) and settings.PRODUCTION:
                elapsed = timezone.now() - customer.sms_code.sended
                if elapsed < timedelta(seconds=30):
                    return Response(
                        data={'detail': 'You too often make a request.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )

            # Отправка СМС на номер
            send_sms_code.delay(customer.username, customer.sms_code.code)

        headers = self.get_success_headers(serializer.data)

        return Response(
            data={'detail': 'SMS successfully sent.'},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
