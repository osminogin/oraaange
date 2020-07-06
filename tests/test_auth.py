import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status


def test_new_token(client, request):
    """ Получение нового токена. """
    data = {
        'username': request.config.test_username,
        'password': request.config.test_password,
    }
    response = client.post(reverse('login'), data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'token' in data
    assert len(data['token']) > 64


def test_refresh_token(client, jwt_token):
    """ Обновление токена из старого. """
    response = client.post(
        reverse('refresh_token'),
        {'token': jwt_token}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'token' in data
    assert len(data['token']) > 64


@pytest.mark.skip(reason='Выключет resfresh_token - работаем на бизлимитных токена.')
def test_no_access_refresh_token(client):
    """ Попытка обновиться c наверным токеном. """
    response = client.post(reverse('refresh_token'), {'token': 'sdsadasdasda'})
    assert response.status_code != status.HTTP_200_OK


def test_sms_code_lifetime(client, example_user, mocker):
    """ Проверка актуального и устаревшего СМС-кода. """
    response = client.post(
        reverse('login'),
        {'username': example_user.username, 'password': example_user.sms_code.code},
    )
    assert response.status_code != status.HTTP_200_OK

    # Исправляем время на текущее, т.е. делаем "свежим"
    from users.models import SMSCode
    example_user.sms_code = SMSCode.objects.create()
    example_user.save()
    response = client.post(
        reverse('login'),
        {'username': example_user.username, 'password': example_user.sms_code.code},
    )
    assert response.status_code == status.HTTP_200_OK
