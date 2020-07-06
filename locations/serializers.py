from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.utils.translation import ugettext_lazy as _


class LocationSerializer(GeoFeatureModelSerializer):
    """
    Location serializer.
    """
    class Meta:
        model = get_user_model()
        geo_field = 'location'
        fields = ('location',)
        extra_kwargs = {
            'location': {'write_only': True, 'required': True}
        }


class WhoIsNearQueryParamsSerializer(serializers.Serializer):
    """ Serializer on query params for who is near. """
    radius = serializers.IntegerField(
        default=10000,
        min_value=1000, max_value=60000, help_text=_('Radius in meters.')
    )
    zoom = serializers.IntegerField(
        required=False, default=10,
        min_value=1, max_value=20, help_text=_('Zoom level (20 max).')
    )


class DetectCountryByIPSerializer(serializers.Serializer):
    """
    Serializer for geoip resolved response.
    """
    ip = serializers.IPAddressField()
    country = serializers.CharField()
    iso_code = serializers.CharField(max_length=2)
