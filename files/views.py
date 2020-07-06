import uuid
from mimetypes import guess_type
from datetime import timedelta, datetime

import minio
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import SuspiciousOperation, ObjectDoesNotExist
from rest_framework import viewsets, mixins, status, parsers, permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from minio.error import ResponseError

from core.serializers import EmptySerializer
from core.permissions import OnlyOwnerAllowedEdit
from core.constants import MULTIMEDIA_FILE_TYPES
from core.utils import get_file_type
from .models import File
from .tasks import FileTask
# from .forms import UploadForm
from .filters import FileFilter
from .serializers import (
    FileSerializer, UploadSerializer, SignQueryParamsSerializer,
    SignedFormDataSerializer, UploadQueryParamsSerializer
)


class FileViewSet(mixins.RetrieveModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    A viewset for files uploading and downloading files.

    retrieve:
        Получение метаданных файла по UUID.
    """
    lookup_field = 'uuid'
    serializer_class = FileSerializer
    queryset = File.objects.is_uploaded()
    permission_classes = (IsAuthenticatedOrReadOnly, OnlyOwnerAllowedEdit,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FileFilter
    http_method_names = ('get', 'post', 'delete',)

    def list(self, request, *args, **kwargs):
        """ Список файлов пользователя. """
        qs = self.get_queryset().filter(user=request.user.pk)
        queryset = self.filter_queryset(qs)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @swagger_auto_schema(
        query_serializer=UploadQueryParamsSerializer,
        responses={405: 'Method Not Allowed.'}
    )
    @action(
        methods=['post'], detail=False,
        serializer_class=UploadSerializer,
        parser_classes=(parsers.MultiPartParser,),
    )
    def upload(self, request):
        """ DEPRECATED. Загрузка файла через форму в хранилище файлов. """
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # form = UploadForm(request.POST, request.FILES)
        # file_name = form.files['file'].name
        # file_type = self._get_file_type(request, file_name)
        #
        # if form.is_valid():
        #     uploaded = request.user.files.create(
        #         file=form.files['file'],
        #         orig_name=file_name,
        #         file_type=file_type,
        #         mime_type=form.files['file'].content_type,
        #         is_uploaded=True
        #     )
        #     # TODO: Нужно посчитать насколько дорогая такая конструкция вообще
        #     data = uploaded.__dict__
        #     data['type'] = data.pop('file_type')
        #     serializer = FileSerializer(data=data)
        #     serializer.is_valid(raise_exception=True)
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # else:
        #     return Response(status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=EmptySerializer,
        query_serializer=SignQueryParamsSerializer,
        responses={201: SignedFormDataSerializer},
    )
    @action(methods=['post'], detail=False)
    def sign(self, request):
        """ Подписание прямой загрузки файла в хранилище. """
        query_serializer = SignQueryParamsSerializer(data=request.GET)
        query_serializer.is_valid(raise_exception=True)

        file_uuid = str(uuid.uuid4())
        orig_name = request.GET['orig_name']
        mime_type = guess_type(orig_name)[0] or 'application/octet-stream'
        file_type = self._get_file_type(request, orig_name)

        post_policy = minio.PostPolicy()
        post_policy.set_bucket_name(settings.AWS_STORAGE_BUCKET_NAME)
        post_policy.set_key(file_uuid)
        post_policy.set_expires(datetime.utcnow() + timedelta(days=1))
        post_policy.set_content_type(mime_type)

        if query_serializer.validated_data.get('type') == 'video':
            post_policy.set_content_length_range(10, 100 * 1 << 20)    # 100 MB
        else:
            post_policy.set_content_length_range(1, 10 * 1 << 50)      # 50 MB

        client = minio.Minio(settings.AWS_S3_ENDPOINT_URL.replace('http://', ''),
                             access_key=settings.AWS_ACCESS_KEY_ID,
                             secret_key=settings.AWS_SECRET_ACCESS_KEY,
                             secure=False)
        # Подписываем загрузку с указанным policy
        try:
            file_data = {
                'uuid': file_uuid,
                'user': request.user,
                'file_type': file_type,
                'orig_name': orig_name,
                'mime_type': mime_type,
                'handler': query_serializer.validated_data.get('handler'),
                'is_private': query_serializer.validated_data['is_private'],
                'is_uploaded': False,
            }

            target_url, signed_form_data = client.presigned_post_policy(post_policy)
            query_params = {
                'target_url': target_url,
                'content-type': mime_type,
                **signed_form_data
            }
            if query_serializer.validated_data.get('duration'):
                audio_duration = query_serializer.validated_data.get('duration')
                query_params['x-amz-meta-duration'] = audio_duration
                file_data['metadata'] = {'duration': audio_duration}

            serializer = SignedFormDataSerializer(data=query_params)
            serializer.is_valid(raise_exception=True)

            # Create new file entry
            assert File.objects.create(**file_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ResponseError as err:
            return Response(
                data={'detail': str(err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def _get_file_type(request, file_name):

        # Тип файла можно форсить через query params
        file_type = request.GET.get('type', None)
        if file_type and \
                file_type not in MULTIMEDIA_FILE_TYPES + [File.Type.DOCUMENT]:
            raise SuspiciousOperation   # Какой-то мусор в значении

        # В обычном случае пытаемся определить тип по расширению
        if not file_type:
            file_type = get_file_type(file_name)

        return file_type


@api_view(['POST'])
@swagger_auto_schema(auto_schema=False)
@permission_classes((permissions.AllowAny,))
def minio_webhook(request):
    """ Вебхук для событий от стораджа. """
    uploaded = False
    data = request.data
    if data['EventName'].startswith('s3:ObjectCreated:'):
        uploaded = True

    file_name = data['Key'] \
        .lstrip(settings.AWS_STORAGE_BUCKET_NAME) \
        .lstrip('/')

    # TODO: Можно так же отлавливать и считать просмотры.

    try:
        uuid.UUID(file_name)
        file = File.objects.get(uuid=file_name)
        if uploaded:
            # Указывается размер и Файл помечается загруженным
            file.is_uploaded = True
            file.file_size = int(data['Records'][0]['s3']['object']['size'])
            file.save()

            # Конвертация файла в асинхронном режиме
            FileTask().delay(str(file.uuid))

    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    except ValueError:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_200_OK)
