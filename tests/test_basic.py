from django.urls import reverse
from rest_framework import status


def test_ping_pong(client):
    """ Ping-pong monitoring check. """
    response = client.get(reverse('ping'))
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b'pong'


def test_docs_index(client, jwt_headers):
    """ Страница документации. """
    response = client.get(reverse('oraaange-docs:docs-index'), **jwt_headers)
    assert response.status_code == status.HTTP_200_OK


def test_wrong_data_input(client):
    """ Проверка неверных параметров на вход. """
    response = client.post(
        reverse('v2:initial-list'),
        {'phone': 'abcdefghklmn123456'}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_restrict_user_middleware(example_user, client, jwt_headers):
    """
    Проверка ограничения доступа для заблокированных пользователей.
    """
    example_user.is_restricted = True
    example_user.save()
    response = client.get(
        reverse('v2:contact-list'), **jwt_headers
    )
    assert response.status_code == status.HTTP_423_LOCKED
