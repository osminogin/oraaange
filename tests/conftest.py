import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core import management
from django.urls import reverse
from rest_framework import status

from ads.models import Ad
from core.utils import get_random_phone
from users.models import SMSCode


def pytest_configure(config):
    config.test_username = '79261935000'
    config.test_password = '1111'
    config.test_device_id = 'cwtlOJg6Q2s:APA91bGd5j8zwBbQPtTuGkOu4YGOYLr1sxJ' \
        'M_M1LCsdcoyRZprAdSPvBhe3IMAEJ3PpFMWuUCA9iI2_BiVvYeBkHL3TeHxRqEdZyNi' \
        'hb6rQgngxkXomoFW424NOB6Ya3_CNR2nuQoxz-'


def pytest_addoption(parser):
    parser.addoption('--online', action='store_true',
                     help='network connection required tests')


@pytest.fixture(scope='session', autouse=True)
def initial_data(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        management.call_command('loaddata', 'initial_data.json')


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope='function')
def jwt_token_by_user(client, request):
    """ JWT token. """
    def getter(user):
        response = client.post(
            reverse('login'),
            data=json.dumps({
                'username': user.username,
                'password': '1111'
            }),
            content_type='application/json',
        )
        assert response.status_code == status.HTTP_200_OK
        return response.data.get('token')

    return getter


@pytest.fixture(scope='function')
def jwt_headers_by_user(jwt_token_by_user):
    """ Headers for JWT auth. """
    def getter(user):
        token = jwt_token_by_user(user)
        return {
            'content_type': 'application/json',
            'HTTP_AUTHORIZATION': f'Bearer {token}'
        }
    return getter


@pytest.fixture(scope='function')
def jwt_token(client, request):
    """ JWT token. """
    response = client.post(
        reverse('login'),
        data=json.dumps({
            'username': request.config.test_username,
            'password': request.config.test_password
        }),
        content_type='application/json',
    )
    assert response.status_code == status.HTTP_200_OK
    yield response.data.get('token')


@pytest.fixture(scope='function')
def jwt_headers(jwt_token):
    """ Headers for JWT auth. """
    yield {
        'content_type': 'application/json',
        'HTTP_AUTHORIZATION': f'Bearer {jwt_token}'
    }


@pytest.fixture(scope='function')
def example_user(request):
    """ Concreate test user. """
    yield get_user_model().objects.get(username=request.config.test_username)


@pytest.fixture(scope='function')
def test_user(request):
    """ Sample test user from initial data. """
    yield get_user_model().objects.exclude(username=request.config.test_username).first()


@pytest.fixture(scope='function')
def another_user():
    """ Another test user. """
    yield get_user_model().objects.create(
        username=get_random_phone(),
        is_active=True,
        confirm_tos=True,
        sms_code=SMSCode.objects.create(),
        location=Point(1.32, 1.12)
    )


@pytest.fixture(scope='function')
def example_ad(example_user):
    """ Test ad. """
    yield Ad.objects.create(
        title='TITLE',
        text='Ad text.',
        ages=(18, 80),
        address='ul. Mira, 8',
        type=Ad.Type.dating,
        user=example_user,
        point=Point(1.32, 1.12),
        is_active=True
    )


@pytest.fixture(scope='function')
def message(chat, example_user):
    """ Message fixture. """
    yield chat.messages.create(text='Text message', sender=example_user)


@pytest.fixture(scope='function')
def chat(example_user, test_user):
    """ Example chat. """
    chat = test_user.owned_chats.create(
        title='Test chat',
        recipients=[example_user.uuid, test_user.uuid]
    )
    chat.messages.create(text='Text message', sender=test_user)
    yield chat


@pytest.fixture(scope='function')
def another_chat(example_user):
    """ Another example chat. """
    chat = example_user.owned_chats.create(
        title='Another test chat',
        recipients=[example_user.uuid]
    )
    chat.messages.create(text='Another text message', sender=example_user)
    yield chat


@pytest.fixture(scope='function')
def geojson_point():
    yield {
        'location': {
            'type': 'Point',
            'coordinates': [125.6, 10.1]
        }
    }


@pytest.fixture(scope='function')
def contact(example_user, test_user):
    """ Пользовательский контакт для тестов. """
    yield example_user.contacts.create(user=test_user, is_from_app=True)
