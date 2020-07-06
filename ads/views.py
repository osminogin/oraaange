from django.contrib.gis.geos import GEOSGeometry
from django.db import connection
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_gis.filters import DistanceToPointFilter, InBBoxFilter
from rest_framework_gis.pagination import GeoJsonPagination

from abuses.serializers import AdAbuseSerializer
from core.utils import (fix_rawsql_helper, get_best_minpoints_dbscan,
                        get_meter_per_pixel, get_rows_from_cursor)
# from core.filters import DistanceToPointFilter
from core.viewsets import CustomModelViewSet

from .filters import AdFilter
from .models import Ad
from .serializers import (AdCollectionQueryParamsSerializer,
                          AdListCollectionSerializer,
                          AdMapCollectionSerializer,
                          AdMapQueryParamsSerializer, AdSerializer)


class AdViewSet(CustomModelViewSet):
    """
    list:
        Return all active ads.
    retrive:
        Return serialized ad instance.
    update:
        Return updated serialized user instance.
    delete:
        Hide adverstimenet from public.

    """
    lookup_field = 'uuid'
    queryset = Ad.objects.all()
    permission_classes = (IsAuthenticated, )
    pagination_class = GeoJsonPagination
    distance_filter_field = 'point'
    distance_filter_convert_meters = True
    bbox_filter_field = 'point'
    bbox_filter_include_overlapping = True
    filter_backends = (InBBoxFilter, DistanceToPointFilter, DjangoFilterBackend,)
    filterset_class = AdFilter
    http_method_names = ('get', 'post', 'patch', 'delete',)

    def retrieve(self, request, *args, **kwargs):
        user_uuid = str(request.user.uuid)
        instance = self.get_object()
        if user_uuid not in instance.viewed_by:
            instance.viewed_by.append(user_uuid)
            instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def get_serializer_class(self):
        """
        Различные методы используют различные сериализаторы.
        """
        if self.action in ('create', 'update', 'partial_update', 'retrieve',):
            return AdSerializer
        elif self.action in ('list',):
            return AdListCollectionSerializer
        elif self.action in ('abuse',):
            return AdAbuseSerializer
        else:
            return AdMapCollectionSerializer

    @swagger_auto_schema(
        query_serializer=AdCollectionQueryParamsSerializer, responses={200: ''}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(responses={201: ''})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_dbscan_sql(self, zoom, points_count, eps=50, minpoints=None):
        """
        RawSQL-реализация алгоритма DBSCAN для предложений.
        """
        minpoints = get_best_minpoints_dbscan(points_count, minpoints)
        queryset = self.filter_queryset(self.get_queryset())
        ads_rawquery = str(queryset.query).rstrip(';')
        # SRID 2956 4326
        sql = f"""
            WITH
                _ads as ({ads_rawquery}),
                clusters as (
                    SELECT
                        ST_ClusterDBSCAN(ST_Transform(point, 4326), {eps}, {minpoints}) OVER() AS cluster_id,
                        uuid, point, created_at, title, text, address, ages, user_id,
                        sex, period, type, False as is_viewed, is_blocked,
                        is_active
                    FROM _ads
                )
            SELECT
                cluster_id,
                uuid,
                point,
                created_at,
                title,
                text,
                address,
                ages,
                user_id,
                sex,
                period,
                type,
                is_active,
                is_blocked,
                '1' AS geom_count,
                False as is_cluster

            FROM clusters WHERE cluster_id IS NULL

            UNION   -- Объединение
            SELECT
                cluster_id,
                '00000000-0000-0000-0000-000000000000'::uuid as uuid,
                ST_Centroid(ST_Collect(clusters.point)) as point,
                NULL as created_at,
                CONCAT('Cluster ', cluster_id) as title,
                '' as text,
                NULL as address,
                NULL as ages,
                NULL as user_id,
                'N' as sex,
                NULL as period,
                NULL as type,
                True as is_active,
                False as is_blocked,
                COUNT(clusters.point) as geom_count,
                True as is_cluster
            FROM clusters
            GROUP BY cluster_id
            HAVING cluster_id >= 0
        """
        return fix_rawsql_helper(sql)

    @action(methods=['get'], detail=False, pagination_class=GeoJsonPagination)
    @swagger_auto_schema(query_serializer=AdMapQueryParamsSerializer,
                         responses={200: ''})
    def map(self, request, *args, **kwargs):
        """
        Предложения для отображения на карте.
        """
        query_serializer = AdMapQueryParamsSerializer(data=request.GET)
        query_serializer.is_valid(raise_exception=True)
        zoom = query_serializer.validated_data.get('zoom')

        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        points_count = queryset.count()
        meter_pixel = get_meter_per_pixel(zoom)

        # При определенном зуме кластеризация не применяется
        if zoom >= 20 or points_count < 3:
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
                    row['point'] = GEOSGeometry(row['point'])
                    # row['uuid'] = str(row['uuid'])

                serializer = self.get_serializer(data, many=True)

        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(methods=['post'], detail=True, serializer_class=AdAbuseSerializer)
    def abuse(self, request, uuid=None):
        instance = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ad=instance, sender=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
