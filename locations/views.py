from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from django.contrib.gis.geoip2 import GeoIP2

from core.utils import get_client_ip
from core.serializers import EmptySerializer
from .serializers import LocationSerializer, DetectCountryByIPSerializer


class LocationViewSet(mixins.CreateModelMixin,
                      viewsets.GenericViewSet):
    """
    ViewSet for locations and geo things.
    """
    queryset = get_user_model().objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)
    distance_filter_field = 'location'
    pagination_class = None
    serializer_class = LocationSerializer

    @swagger_auto_schema(responses={200: 'User geolocation updated.'})
    def create(self, request, *args, **kwargs):
        """ Updates user location. """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.location = serializer.validated_data['location']
        self.request.user.save()

        headers = self.get_success_headers(serializer.data)
        return Response(status=status.HTTP_200_OK, headers=headers)

    @swagger_auto_schema(
        responses={
            200: DetectCountryByIPSerializer,
            404: 'Can\'t detect country by IP.'
        },
        query_serializer=EmptySerializer
    )
    @action(methods=['get'], detail=False, permission_classes=(AllowAny,))
    def detect(self, request):
        """ Определение страны пользователя по IP (GeoIP). """
        ip = get_client_ip(request)
        g = GeoIP2()
        match = g.country(ip)
        if not match:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = DetectCountryByIPSerializer(
            data={
                'country': match['country_name'],
                'iso_code': match['country_code'],
                'ip': ip
            }
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
