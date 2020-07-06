"""
Тестирование фнукцинальных методов.

Соответсвтвие бексенда ФТ и ТЗ.
"""
import json
import random

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

from core.utils import get_jwt_payload
from users.serializers import UserSerializer


def test_authentication(geojson_point, client, jwt_headers, request):
    """ Тестирования модуль "Авторизация". Первая часть. """

    test_phone = random.randint(79260000000, 79269999999)

    # Е-3-1
    # Осуществлять регистрацию пользователя при первом входе

    response = client.post(
        reverse('v2:initial-list'),
        data={'phone': str(test_phone)}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['detail'] == 'SMS successfully sent.'

    # TODO: Поставить проверку мокером метода на отправку таска в селери

    # ЕS-3-1.1
    # Осуществлять подтверждение номера телефона пользователя

    response = client.post(
        reverse('login'),
        data={
            'username': str(test_phone),
            'password': request.config.test_password
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'token' in data
    assert 'new_user' in data
    assert data['new_user'] is True     # Пользователь - "свежерег"

    # Все последующие запросы с токеном этого нового пользователя
    token = data['token']
    jwt_headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    token_payload = get_jwt_payload(token)
    user = get_user_model().objects.get(pk=token_payload['user_id'])

    # ES-3-1.2
    # Осуществлять сбор минимально необходимой информации о пользователе
    # для регистрации в приложении.

    # ES-3-1.3
    # Получить согласие пользователя с условиями обслуживания и обработкое
    # его персональных данных.

    # Выставляем поля, что бы пользоавтель в итоге проходил регу
    response = client.patch(
        reverse('v2:user-detail', kwargs={'uuid': user.uuid}),
        json.dumps({
            'display_name': 'Vladimir Putin',
            'birth_date': '2018-05-21',
            'sex': 'M',
            'im_confirm_tos': True,
        }),
        **jwt_headers
    )

    assert response.status_code == status.HTTP_200_OK
    # Проверяем полученную модель пользователя сериализатором
    serializer = UserSerializer(data=response.data)
    assert serializer.is_valid()

    # E-3-4
    # Осуществлять выход пользователя из своей учетной записи
    # На клиенте вычишается token - это и есть logout


def test_authentication_second(client, admin_client, jwt_headers, request):
    """ Тестирования модуль "Авторизация". Вторая часть. """

    # Е-3-2
    # Осуществлять повторный вход пользователя в приложение с того же устройства

    # Е-3-3
    # Осуществлять вход в приложение с другого мобильного устройства или
    # при переустановке приложения по зарегистрированному номеру телефону /
    # при выходе из учетной записи

    response = client.post(
        reverse('login'),
        data={
            'username': request.config.test_username,
            'password': request.config.test_password
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'token' in data
    assert 'new_user' not in data
