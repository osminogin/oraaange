import datetime
import json
import mimetypes
import os
import tempfile
import uuid
from pathlib import Path

import pytest
import requests
from django.conf import settings
from django.http import QueryDict
from django.urls import reverse
from minio import Minio
from PIL import Image
from rest_framework import status

from core.utils import get_file_type
from files.models import File
from files.serializers import FileSerializer, SignedFormDataSerializer
from files.tasks import FileTask


@pytest.fixture(scope='function')
def sample_file():
    """ Открытый дескриптор тестового файла. """
    fp = open(Path.cwd() / 'README.md')
    yield fp
    fp.close()


@pytest.fixture(scope='function')
def sample_image_file():
    """ Именованный временный файл (присутсвует на файловой системе). """
    fp = tempfile.NamedTemporaryFile(delete=False)
    fp.close()
    image = Image.new('RGB', (1024, 768), color='grey')
    image.save(fp.name, format='PNG')
    yield fp
    os.unlink(fp.name)


@pytest.fixture(scope='function')
def user_with_files(example_user, sample_image_file, settings):
    file_name = sample_image_file.name
    assert example_user.files.create(
        file=file_name,
        orig_name=file_name,
        file_type=get_file_type(file_name),
        mime_type=mimetypes.guess_type(file_name)[0]
    )
    yield example_user


@pytest.mark.skip(reason='Метод помечен как deprecated.')
def test_api_some_file_upload(sample_file, client, jwt_token, settings):
    """ Загруза тестового файла на сервер. """
    settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    response = client.post(
        reverse('v2:file-upload'),
        data={'file': sample_file},
        format='multipart',
        HTTP_AUTHORIZATION=f'Bearer {jwt_token}'
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    serializer = FileSerializer(data=response.data)
    assert serializer.is_valid()
    assert serializer.data['type'] == 'document'
    assert serializer.data['url'].endswith(data['uuid'])


# def test_api_some_file_speech_upload(sample_file, chat, client, jwt_token, settings):
#     """ Загруза тестового файла в режиме рации. """
#     settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
#     response = client.post(
#         reverse('v2:chat-speech', kwargs={'uuid': chat.uuid}),
#         data={'file': sample_file},
#         format='multipart',
#         HTTP_AUTHORIZATION=f'Bearer {jwt_token}'
#     )
#
#     assert response.status_code == status.HTTP_201_CREATED
#     data = response.json()
#     serializer = FileSerializer(data=response.data)
#     assert serializer.is_valid()
#     assert serializer.data['type'] == 'document'
#     assert serializer.data['url'].endswith(data['uuid'])


@pytest.mark.skip(reason='Метод помечен как deprecated.')
def test_api_file_upload_force_type(sample_file, client, jwt_token, settings):
    """ Форсим тип загружаймого файла через query params. """
    settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    q = QueryDict('', mutable=True)
    q['type'] = 'image'
    response = client.post(
        reverse('v2:file-upload') + f'?{q.urlencode()}',
        data={'file': sample_file},
        format='multipart',
        HTTP_AUTHORIZATION=f'Bearer {jwt_token}'
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    serializer = FileSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.data['type'] == 'image'
    assert serializer.data['url'].endswith(data['uuid'])


def test_api_list_user_files(user_with_files, client, jwt_headers):
    """ Полный список загруженных юзером файлов (без фильтрации). """
    response = client.get(
        reverse('v2:file-list'),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()['results']
    assert len(data) == user_with_files.files.is_uploaded().count()
    serializer = FileSerializer(data=data, many=True)
    assert serializer.is_valid()


def test_api_retrieve_some_files(client, test_user):
    """ Получение матаданных файла. """
    file_uuid = test_user.files.first().uuid
    response = client.get(reverse('v2:file-detail', kwargs={'uuid': file_uuid}))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    serializer = FileSerializer(data=data)
    assert serializer.is_valid()
    # TODO: update is_compressed
    # assert serializer.data['url'].endswith(data['uuid'])


def test_api_sign_method(client, example_user, jwt_headers):
    file_name = 'example.dat'
    q = QueryDict('', mutable=True)
    q['orig_name'] = file_name
    q['is_private'] = 1
    response = client.post(
        reverse('v2:file-sign') + f'?{q.urlencode()}',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.webtest
def test_api_sign_file_upload(client, sample_file, jwt_headers):
    """ Загрузка файла по pre-signed url. """
    q = QueryDict('', mutable=True)
    q['orig_name'] = sample_file.name
    q['durartion'] = 120
    response = client.post(
        reverse('v2:file-sign') + f'?{q.urlencode()}',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    serializer = SignedFormDataSerializer(data=response.data)
    assert serializer.is_valid()

    del response.data['target_url']
    response = requests.post(
        serializer.validated_data['target_url'],
        files={'file': sample_file},
        data=response.data,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.webtest
def test_minio_presigned_put_object():
    """ Альтернативный способ загрузки через PUT на presigned url. """
    client = Minio(settings.AWS_S3_ENDPOINT_URL.replace('http://', ''),
                   access_key=settings.AWS_ACCESS_KEY_ID,
                   secret_key=settings.AWS_SECRET_ACCESS_KEY,
                   secure=False)

    presigned_url = client.presigned_put_object(
        settings.AWS_STORAGE_BUCKET_NAME,
        str(uuid.uuid4()),
        datetime.timedelta(days=3)
    )
    assert presigned_url


# @pytest.mark.webtest
def test_api_sign_file_with_metadata(client, sample_file, jwt_headers):
    """ Подписание файла с метаданными """
    file_name = 'example.mp3'
    test_duration = 120
    q = QueryDict('', mutable=True)
    q['orig_name'] = file_name
    q['duration'] = test_duration
    q['handler'] = File.Handler.AUDIO_ENCODING
    response = client.post(
        reverse('v2:file-sign') + f'?{q.urlencode()}',
        **jwt_headers
    )   # Empty POST request
    assert response.status_code == status.HTTP_201_CREATED
    file = File.objects.get(orig_name=file_name)
    assert file.handler == File.Handler.AUDIO_ENCODING
    assert 'duration' in file.metadata
    assert file.metadata['duration'] == str(test_duration)

    serializer = SignedFormDataSerializer(data=response.data)
    assert serializer.is_valid()

    del response.data['target_url']
    response = requests.post(
        serializer.validated_data['target_url'],
        files={'file': sample_file},
        data=response.data,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = requests.head(response.headers['location'])
    assert 'x-amz-meta-duration' in response.headers
    assert response.headers['x-amz-meta-duration'] == str(test_duration)


def test_api_sign_method_with_handler(client, jwt_headers):
    """ Подписание файла на загрзку с определенным обработчиком. """
    file_name = 'example.png'
    response = client.post(
        reverse('v2:file-sign') + f'?orig_name={file_name}&handler={File.Handler.AVATAR}',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert File.objects.get(orig_name=file_name).handler == File.Handler.AVATAR


def test_api_delete_file(client, user_with_files, jwt_headers):
    get_files_count = lambda: user_with_files.files.count()
    files_count = get_files_count()
    response = client.delete(
        reverse('v2:file-detail', kwargs={'uuid': user_with_files.files.first().uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert files_count - 1 == get_files_count()


@pytest.mark.minio
def test_minio_upload_webhook(client, example_user, jwt_headers):
    """ Проверка прилетающего вебхука от стораджа. """
    file_uuid = str(example_user.files.first().uuid)
    data = {
        'EventName': 's3:ObjectCreated:Post',
        'Key': f'limon-files/',
        'Records': [{
            'eventVersion': '2.0',
            'eventSource': 'minio:s3',
            'awsRegion': '',
            'eventTime': '2018-10-04T11:47:14Z',
            'eventName': 's3:ObjectCreated:Put',
            'userIdentity': {
                'principalId': 'AF0K4QVKX3KN7VHZ7A8A'
            },
            'requestParameters': {
                'sourceIPAddress': '89.17.62.222'
            },
            'responseElements': {
                'x-amz-request-id': '155A65540F55CDA1',
                'x-minio-origin-endpoint': 'http://127.0.0.1:9000'
            },
            's3': {
                's3SchemaVersion': '1.0',
                'configurationId': 'Config',
                'bucket': {
                    'name': 'limon-files',
                    'ownerIdentity': {
                        'principalId': 'AF0K4QVKX3KN7VHZ7A8A'
                    },
                    'arn': 'arn:aws:s3:::limon-files'
                },
                'object': {
                    'key': '',
                    'size': 2547,
                    'eTag': '70eda23e9d577b106932ff1c98e5b4ec',
                    'contentType': 'image/png',
                    'userMetadata': {
                        'content-type': 'image/png'
                    },
                    'versionId': '1',
                    'sequencer': '155A65540F55CDA1'
                }
            },
            'source': {
                'host': '',
                'port': '',
                'userAgent': 'Minio (linux; amd64) minio-go/v6.0.6 mc/2018-09-10T23:39:12Z'
            }
            }]
    }
    # response = client.post(
    #     reverse('file-webhook'),
    #     data=json.dumps(data),
    #     **jwt_headers
    # )
    # assert response.status_code == status.HTTP_200_OK


# def test_file_task_compress_avatar(example_user, mocker):
#     file = example_user.files.first()
#     file.handler = File.Handler.AVATAR
#     file.save()
#
#     from unittest.mock import mock_open
#     m = mock_open()
#     mocker.patch('builtins.open', m, create=True)
#     FileTask().delay(str(file.uuid))
