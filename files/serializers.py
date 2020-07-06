import os
from collections import OrderedDict

from django.conf import settings
from rest_framework import serializers

from core.fields import TimestampField

from .models import File


class FileSerializer(serializers.ModelSerializer):
    """
    File object serializator.
    """
    uuid = serializers.UUIDField()
    size = serializers.IntegerField(source='file_size', allow_null=True)
    url = serializers.SerializerMethodField()
    timestamp = TimestampField(source='created_at', required=False)
    type = serializers.CharField(source='file_type')
    metadata = serializers.HStoreField(allow_null=True, read_only=False)

    class Meta:
        model = File
        fields = (
            'uuid', 'orig_name', 'url', 'size', 'type', 'mime_type',
            'timestamp', 'is_uploaded', 'is_compressed', 'metadata',
        )

    @staticmethod
    def get_size(obj) -> int:
        """ Размер файла в байтах (не зависит от типа стораджа). """
        return getattr(obj, 'size', getattr(obj, 'file.size', None))

    @staticmethod
    def get_url(obj):
        """ Публичный URL для доступа к файлу. """
        is_dict = isinstance(obj, OrderedDict)
        if is_dict and not obj['is_compressed']:
            return None

        if not is_dict and not obj.is_compressed:
            return None

        if isinstance(obj, OrderedDict):
            # Через @action сюда приходит OrderedDict - конвертим в обычный
            data = dict(obj)
        else:
            data = {'uuid': obj.uuid}

        public_url = os.path.join(
            settings.AWS_S3_ENDPOINT_URL,
            settings.AWS_STORAGE_BUCKET_NAME,
            str(data['uuid'])
        )
        return public_url


class UploadSerializer(serializers.ModelSerializer):
    """
    Uploaded file serializator.
    """
    class Meta:
        model = File
        fields = ('file',)


class UploadQueryParamsSerializer(serializers.Serializer):
    """ Serializer on query params on file upload. """
    type = serializers.ChoiceField(choices=File.Type.choices, required=False)


class SignQueryParamsSerializer(UploadQueryParamsSerializer):
    """
    Pre-signed upload query params serializer.
    """
    orig_name = serializers.CharField(max_length=100, required=True)
    duration = serializers.IntegerField(min_value=1, required=False)
    handler = serializers.ChoiceField(
        choices=File.Handler.choices,
        required=False,
        allow_null=True
    )
    is_private = serializers.BooleanField(default=False, required=False)


class SignedFormDataSerializer(serializers.Serializer):
    """
    Pre-signed form data ready for direct upload.
    """
    bucket = serializers.CharField()
    key = serializers.UUIDField()
    policy = serializers.CharField()
    x_amz_algorithm = serializers.CharField()
    x_amz_credential = serializers.CharField()
    x_amz_date = serializers.CharField()
    x_amz_signature = serializers.CharField()
    x_amz_meta_duration = serializers.IntegerField(required=False)
    target_url = serializers.URLField()
    content_type = serializers.CharField()

    def __init__(self, *args, **kwargs):
        """ Заменяет в специальных полях знак подчеркивания на тире. """
        super().__init__(*args, **kwargs)
        for key in list(self.fields.keys()):
            if key.startswith('x_') or key == 'content_type':
                field = self.fields.pop(key)
                self.fields[key.replace('_', '-')] = field
