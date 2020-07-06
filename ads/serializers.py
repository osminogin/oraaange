from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from core.fields import ArrayToggleField, TimestampField, TimestampRangeField
from core.serializers import validate_toggle_field
from users.serializers import SimpeUserSerializer

from .models import Ad


class AdSerializer(serializers.ModelSerializer):
    """
    Ads serializer.
    """
    period = TimestampRangeField(required=False)
    desired_age = serializers.SerializerMethodField()
    timestamp = TimestampField(source='created_at', read_only=True)
    is_favorited = ArrayToggleField(source='favorited_for', required=False)
    is_viewed = ArrayToggleField(
        source='viewed_by',
        read_only=True,
        required=False
    )

    user = SimpeUserSerializer(read_only=True)

    class Meta:
        model = Ad
        fields = (
            'uuid', 'user', 'type', 'point', 'sex', 'title', 'text', 'period',
            'desired_age', 'ages', 'timestamp', 'address',
            'is_active', 'is_blocked', 'is_favorited', 'is_viewed'
        )
        read_only_fields = ('is_blocked',)
        extra_kwargs = {
            'ages': {'write_only': True, 'required': False},
            'sex': {'required': False},
            'point': {'required': False}
        }

    @staticmethod
    def get_desired_age(obj):
        if isinstance(obj, dict):
            if obj.get('ages'):
                return obj['ages'].lower, obj['ages'].upper
        else:
            return obj.ages.lower, obj.ages.upper

    def validate(self, data):
        period = data.get('period')
        period_types = (Ad.Type.meeting, Ad.Type.travel)
        if data.get('type') in period_types and not period:
            raise ValidationError({'period': 'Is required'})

        result = super().validate(data)
        result = validate_toggle_field(
            self.context['request'], self.instance, result, 'favorited_for'
        )
        return result


class AdCollectionQueryParamsSerializer(serializers.Serializer):
    pass
    # in_bbox = serializers.ListField(
    #     min_length=4, max_length=4,
    #     child=serializers.IntegerField(), required=False,
    #     help_text=_('Bounding Box (left_lng,left_lat,right_lng,right_lat).')
    # )
    # in_bbox = serializers.CharField(required=False)
    # is_archive = serializers.BooleanField(required=False)


class AdMapQueryParamsSerializer(AdCollectionQueryParamsSerializer):
    """ Serializer query params for ads map. """
    zoom = serializers.FloatField(
        required=False,
        default=11,
        min_value=1, max_value=21, help_text=_('Zoom level (from 1 to 20).')
    )


class AdMapCollectionSerializer(GeoFeatureModelSerializer):
    """
    Serializer with GeoJSON.
    """
    period = TimestampRangeField(required=False)
    desired_age = serializers.SerializerMethodField()
    timestamp = TimestampField(source='created_at', read_only=True)
    is_cluster = serializers.SerializerMethodField()
    geom_count = serializers.IntegerField(min_value=1, default=1)

    class Meta:
        model = Ad
        geo_field = 'point'
        bbox_filter_field = 'point'
        fields = (
            'uuid', 'type', 'point', 'sex', 'title', 'text', 'period',
            'desired_age', 'ages', 'timestamp', 'address', 'geom_count',
            'is_active', 'is_blocked', 'is_cluster',
            # 'is_favorited', 'is_viewed',
        )
        read_only_fields = ('is_blocked',)
        extra_kwargs = {
            'ages': {'write_only': True, 'required': False},
            'sex': {'required': False},
            'point': {'required': True}
        }

    @staticmethod
    def get_desired_age(obj):
        if isinstance(obj, dict):
            if obj.get('ages'):
                return obj['ages'].lower, obj['ages'].upper
        else:
            return obj.ages.lower, obj.ages.upper

    @staticmethod
    def get_is_cluster(obj) -> bool:
        """ Признак кластера точек. """
        if isinstance(obj, dict) and obj['title'].startswith('Cluster'):
            return True
        return False


class AdListCollectionSerializer(AdMapCollectionSerializer):

    user = SimpeUserSerializer(read_only=True)

    class Meta(AdMapCollectionSerializer.Meta):
        fields = (
            'uuid', 'type', 'point', 'sex', 'title', 'text', 'period',
            'desired_age', 'ages', 'timestamp', 'address',
            'is_active', 'is_blocked', 'user',
        )
