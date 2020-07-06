from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework_gis.serializers import (GeoFeatureModelSerializer,
                                            GeometryField)

from core.fields import TimestampField
from core.utils import get_public_url, get_user_or_create
from files.models import File
from files.serializers import FileSerializer

from .validators import InternationNubmerValidator


class SimpeUserSerializer(serializers.ModelSerializer):
    """
    Simple user serializer.
    """
    age = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    last_activity = TimestampField(read_only=True)
    last_login = TimestampField(read_only=True, source='last_activity')

    class Meta:
        model = get_user_model()
        fields = (
            'uuid', 'display_name', 'age', 'avatar_uuid', 'avatar_url',
            'last_login', 'last_activity', 'is_online',
        )
        extra_kwargs = {
            'avatar_uuid': {'write_only': True, 'required': False},
        }

    @staticmethod
    def get_avatar_url(obj) -> str:
        if obj.avatar_uuid:
            return get_public_url(obj.avatar_uuid, prefix='av')

    @staticmethod
    def get_age(obj) -> int:
        if obj.birth_date:
            return datetime.utcnow().year - obj.birth_date.year


class UserSerializer(serializers.ModelSerializer):
    """
    User serializer.
    """
    last_location = GeometryField(source='location', allow_null=True)
    last_login = TimestampField(read_only=True)
    last_activity = TimestampField(allow_null=True, required=False)
    created_at = TimestampField(source='date_joined', read_only=True)
    phone = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField(read_only=True)
    portfolio = serializers.SerializerMethodField()
    im_confirm_tos = serializers.BooleanField(
        source='confirm_tos',
        write_only=True,
        default=False
    )
    is_contact = serializers.BooleanField(read_only=True)
    is_favorite = serializers.BooleanField(read_only=True)
    is_blocked = serializers.BooleanField(read_only=True)

    class Meta:
        model = get_user_model()
        geo_field = 'location'
        fields = (
            'uuid', 'display_name', 'birth_date', 'email', 'phone',
            'sex', 'age', 'last_login', 'last_location', 'created_at',
            'im_confirm_tos', 'device_id', 'avatar_uuid', 'avatar_url',
            'is_contact', 'is_favorite', 'is_blocked', 'is_online',
            'last_activity', 'show_activity', 'portfolio',
        )
        extra_kwargs = {
            'avatar_uuid': {'write_only': True, 'required': False},
            'email': {'write_only': True, 'required': False},
            'device_id': {'write_only': True},
        }

    def get_portfolio(self, obj):
        qs = obj.files.filter(file_type=File.Type.PORTFOLIO, is_uploaded=True)
        serializers = FileSerializer(qs, many=True)
        return serializers.data

    @staticmethod
    def get_is_online(obj) -> bool:
        if obj.show_activity:
            return obj.is_online
        return False

    def get_last_location(self, obj):
        if obj.show_activity:
            return self.last_location.to_representation(obj.location)
        return None

    def get_phone(self, obj):
        """ Возвращает номер телефона только для текущего пользователя. """
        request = self.context.get('request')
        if request and request.user.is_authenticated and \
                request.user.uuid == obj.uuid:
            return obj.username

    @staticmethod
    def get_avatar_url(obj) -> str:
        if obj.avatar_uuid:
            return obj.get_avatar_url()

    @staticmethod
    def get_age(obj) -> int:
        if obj.birth_date:
            return datetime.utcnow().year - obj.birth_date.year


class InitialSerializer(serializers.ModelSerializer):
    """
    Serializer for initial stage.
    """
    phone = serializers.CharField(
        validators=[InternationNubmerValidator()],
        source='username',
        help_text='Phone number in international format (only numbers).'
    )

    class Meta:
        model = get_user_model()
        fields = ('phone',)

    def create(self, validated_data):
        """
        Возвращает нового зарегистрированного пользователя или существующего.
        """
        return get_user_or_create(**validated_data)


class ImOnlineSerializer(serializers.ModelSerializer):
    """
    Serializer for I'm Online status.
    """
    last_activity = TimestampField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('last_activity', 'is_online')


class UserLocationSerializer(GeoFeatureModelSerializer):
    """
    User location serializer.
    """
    is_cluster = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    geom_count = serializers.IntegerField(min_value=1, default=1)

    class Meta:
        model = get_user_model()
        geo_field = 'location'
        bbox_filter_field = 'location'
        fields = (
            'uuid', 'display_name', 'location', 'is_cluster', 'avatar_url',
            'geom_count',
        )
        extra_kwargs = {
            'location': {'required': True},
            'geom_count': {'required': False},
        }

    @staticmethod
    def get_is_cluster(obj) -> bool:
        """ Признак кластера точек. """
        if isinstance(obj, dict) and obj['display_name'].startswith('Cluster'):
            return True
        return False

    @staticmethod
    def get_avatar_url(obj) -> str:
        if isinstance(obj, dict) and obj.get('avatar_uuid'):
            return get_public_url(obj['avatar_uuid'], prefix='av')
        if isinstance(obj, get_user_model()) and obj.avatar_uuid:
            return obj.get_avatar_url()


class WhoIsNearListQueryParamsSerializer(serializers.Serializer):
    """ Serializer on query params for who is near list. """
    radius = serializers.IntegerField(
        required=True,
        min_value=50, max_value=250000, help_text=_('Radius in meters.')
    )
    # XXX: Переделать
    age = serializers.CharField(
        required=False, help_text=_('Age range (example "20-30").')
    )
    # XXX: Переделать
    in_bbox = serializers.CharField(
        required=False,
        help_text=_('Bounding Box (example "35.62,54.98,38.03,56.07").')
    )


class WhoIsNearMapQueryParamsSerializer(WhoIsNearListQueryParamsSerializer):
    """ Serializer query params for who is near map. """
    zoom = serializers.FloatField(
        required=False,
        default=11,
        min_value=1, max_value=21, help_text=_('Zoom level (from 1 to 20).')
    )
    # Для K-means
    clusters_number = serializers.IntegerField(
        min_value=0, default=3, help_text=_('Number of point clusters on map.')
    )
    # Для DBSCAN
    minpoints = serializers.IntegerField(
        required=False,
        default=2
    )
    eps = serializers.FloatField(
        required=False,
        min_value=0.00000001,
        # default=0.0001
    )
    # Размер горизонтали экрана в пикселях
    horizonta_px = serializers.IntegerField(
        min_value=1, max_value=10240, required=False,
        help_text=_('Horizontal pixels of users screen.')
    )
