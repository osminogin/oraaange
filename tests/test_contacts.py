import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from core.utils import get_random_phone


def test_get_contact_list(contact, client, example_user, jwt_headers):
    """ Запрос контакт-листа для текущего пользователя. """
    response = client.get(reverse('v2:contact-list'), **jwt_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()['results']) == example_user.contacts.count()


def test_delete_from_contact(contact, example_user, client, jwt_headers):
    """ Удаление пользователя из контакта-листа. """
    assert example_user.contacts.count() == 1
    response = client.delete(
        reverse('v2:contact-detail', kwargs={'uuid': contact.user.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert example_user.contacts.count() == 0


def test_favorite_contact(contact, test_user, example_user, client, jwt_headers):
    """ Помечаем контакт как 'избранный'. """
    assert example_user.contacts.filter(is_favorite=True).count() == 0
    response = client.patch(
        reverse('v2:contact-detail', kwargs={'uuid': contact.user.uuid}),
        json.dumps({'is_favorite': True}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert example_user.contacts.filter(is_favorite=True).count() == 1


def test_favorite_list_contacts(contact, client, example_user, jwt_headers):
    """ Список избранных контактов. """
    example_user.contacts.update(is_favorite=True)
    response = client.get(
        reverse('v2:contact-list'),
        {'is_favorite': True},
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == example_user.contacts \
        .filter(is_favorite=True) \
        .count()


def test_import_registered_contacts(contact, client, example_user, jwt_headers):
    """
    Получение списка зарегистрированных пользователей из номеров телефонов.
    """
    # Create registered users for test import
    importing_count = 3
    importing_data = {'contacts': []}
    for i in range(importing_count):
        random_phone = get_random_phone()
        get_user_model().objects.create(
            username=random_phone, is_active=True, confirm_tos=True
        )
        importing_data['contacts'].append({'phone': random_phone})

    # Test import
    response = client.post(
        reverse('v2:contact-import'),
        data=json.dumps(importing_data),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert example_user.contacts.filter(is_from_app=False).count() == importing_count


def test_filter_contacts_is_from_app(contact, client, example_user, jwt_headers):
    """ Фильтрация списка по юзерам, которые были добавлены в приложении. """
    response = client.get(
        reverse('v2:contact-list'),
        {'is_from_app': True},
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == example_user.contacts \
        .filter(is_from_app=True) \
        .count()

    response = client.get(
        reverse('v2:contact-list'),
        {'is_from_app': False},
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == example_user.contacts \
        .filter(is_from_app=False) \
        .count()


def test_contact_list_unauthorized(client):
    """
    Нет доступа к контакт-листу для неавторизованного пользоватя.
    """
    response = client.get(reverse('v2:contact-list'))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_add_new_user_contact_list(client, example_user, another_user, jwt_headers):
    """ Добавление нового пользователя в контакт-лист. """
    contacts_count = example_user.contacts.count()
    response = client.post(
        reverse('v2:contact-add', kwargs={'uuid': another_user.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert example_user.contacts.count() == contacts_count + 1


def test_new_contact_favorite(client, example_user, test_user, jwt_headers):
    """
    Блокировка пользователя автоматически добавляет его в текущий контакт-лист.
    """
    get_favorite_count = lambda: example_user.contacts.filter(is_favorite=True).count()
    favorite_count = get_favorite_count()
    response = client.patch(
        reverse('v2:contact-detail', kwargs={'uuid': test_user.uuid}),
        data=json.dumps({'is_favorite': True}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert favorite_count + 1 == get_favorite_count()
