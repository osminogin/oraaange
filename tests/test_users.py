import json
import random
import string
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from users.serializers import UserSerializer


@pytest.fixture(scope='function')
def user():
    """ Пример объявления. """
    yield get_user_model().objects.create(
        sex='M',
        date_joined=timezone.now(),
        display_name='efimchuk',
    ).interests.add('all')


@pytest.fixture(scope='function')
def blocked_user(example_user, test_user):
    """ Заблокированный пользователь. """
    example_user.black_list.add(test_user)
    yield test_user
    example_user.black_list.remove(test_user)


@pytest.mark.skip(reason='Устаревшая вьюха листинга пользователей.')
def test_user_list_unauthorized(client):
    """ Нет доступа к листингу пользователей для неавторизованного пользоватя. """
    # XXX: Не отдавать список всех пользователей!
    response = client.get(reverse('v2:user-list'))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.skip(reason='Устаревшая вьюха листинга пользователей.')
def test_user_list_locations(client, jwt_headers):
    """ Сериализованный список локаций пользователей. """
    response = client.get(reverse('v2:user-list'), **jwt_headers)
    assert response.status_code == status.HTTP_200_OK
    user_locations_count = response.data['count']
    assert user_locations_count == 2
    assert 'type' in response.data['results']
    assert 'features' in response.data['results']


@pytest.mark.skip(reason='Интересы пока в неактуальном состоянии.')
def test_user_list_include_interests(user, client, jwt_headers):
    """ Сериализованный список пользователей. """
    response = client.get(reverse('v2:user-list'), data={'interests': ['all']}, **jwt_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()['results']
    assert len(data) == 1
    response = client.get(reverse('v2:user-list'), data={'interests': ['test']}, **jwt_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()['results']
    assert len(data) == 0


def test_register_user(client):
    """ Регистрация пользователя. """
    response = client.post(
        reverse('v2:initial-list'),
        {'phone': '71234567890'}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert 'detail' in data
    assert data['detail'] == 'SMS successfully sent.'


def test_user_update_location(client, example_user, jwt_headers):
    """ Обновление локации пользователя. """
    data = {
        'last_location': {
            'type': 'Point',
            'coordinates': [13.0, 42.42]
        }
    }
    response = client.patch(
        reverse('v2:user-detail', kwargs={'uuid': example_user.uuid}),
        json.dumps(data),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    response_data = response.json()
    for key, value in data.items():
        assert key in response_data
        assert response_data[key] == value


@pytest.mark.skip(reason='Горячка. Жалоб не поступало.')
@pytest.mark.parametrize('age_range,user_count', [
    ('30-40', 1),
    ('30-50', 1),
    ('60-70', 0),
    ('20-80', 1),
])
def test_user_age_filter(client, age_range, user_count, jwt_headers):
    """ Фильтр пользователей по возрасту. """
    params = {
        'age': age_range,
        'radius': 250000,
        # 'minpoints': 2,
    }
    response = client.get(
        reverse('v2:user-who'), params, **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['features']) == user_count


def test_wrong_registration_number(client):
    """ Проверка с невалидным номером телефона."""
    response = client.post(
        reverse('v2:initial-list'),
        {'phone': 'dadadasdd82adsadsadas'}
    )
    assert response.status_code != status.HTTP_201_CREATED


def test_user_registration_data(client, example_user, jwt_headers):
    """ Обнволение профиля на последем этапе регистрации. """
    data = {
        'display_name': 'Test User2',
        'email': 'testuser@example.com',
        'birth_date': '1990-01-01',
        'sex': 'F'
    }
    response = client.patch(
        reverse('v2:user-detail', kwargs={'uuid': str(example_user.uuid)}),
        json.dumps(data),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    for key in data:
        if key == 'email':
            continue
        assert response.data[key] == data[key]


def test_restrict_users_without_location(client, example_user, jwt_headers):
    """
    При отсутсвии гелокации пользователя получает 424 Failed Dependency.
    """
    example_user.location = None
    example_user.save()
    response = client.get(
        reverse('v2:user-detail', kwargs={'uuid': str(example_user.uuid)}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_424_FAILED_DEPENDENCY


def test_restrict_blocked_users(client, example_user, jwt_headers):
    """ Заблокираванные пользовати получают 423 Locked. """
    example_user.is_restricted = True
    example_user.save()
    response = client.get(
        reverse('v2:user-detail', kwargs={'uuid': str(example_user.uuid)}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_423_LOCKED


def test_user_upload_set_avatar(client, example_user, jwt_headers):
    """  """
    request = {
        'avatar_uuid': str(uuid.uuid4())
    }
    response = client.patch(
        reverse('v2:user-detail', kwargs={'uuid': example_user.uuid}),
        data=json.dumps(request),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'avatar_url' in response.data
    serializer = UserSerializer(data=response.data)
    assert serializer.is_valid()


def test_user_init_with_existed_username(client, example_user):
    """ Пробуем инит с уже существующим пользователем. """
    response = client.post(
        reverse('v2:initial-list'),
        {'phone': example_user.username}
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_user_get_profile_with_phone(client, example_user, test_user, jwt_headers):
    """ Поле phone отображается только для текущего пользователя. """
    response = client.get(
        reverse('v2:user-detail', kwargs={'uuid': example_user.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'phone' in response.data
    assert response.data['phone'] == example_user.username

    # Another user request profile
    response = client.get(
        reverse('v2:user-detail', kwargs={'uuid': test_user.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'phone' in response.data
    assert response.data['phone'] is None


def test_user_update_device_id(client, example_user, jwt_headers):
    """ Проверка обнволения device_id пользователя. """
    _device_id = ''.join(random.choice(string.ascii_letters) for _ in range(152))
    response = client.patch(
        reverse('v2:user-detail', kwargs={'uuid': example_user.uuid}),
        json.dumps({'device_id': _device_id}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert get_user_model().objects.get(pk=example_user.pk).device_id == _device_id


def test_user_profile_contact_favorite(client, contact, jwt_headers):
    """ Поля связанные с контакт-листом на странице профиля. """
    response = client.get(
        reverse('v2:user-detail', kwargs={'uuid': contact.user.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'is_contact' in response.data
    assert 'is_favorite' in response.data
    assert response.data['is_contact'] is True
    assert response.data['is_favorite'] is False

    # Mark user favorite
    contact.is_favorite = True
    contact.save()
    response = client.get(
        reverse('v2:user-detail', kwargs={'uuid': contact.user.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data['is_favorite'] is True


def test_user_profile_is_blocked(client, blocked_user, contact, jwt_headers):
    """ Поля связанные с контакт-листом на странице профиля. """
    response = client.get(
        reverse('v2:user-detail', kwargs={'uuid': blocked_user.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'is_blocked' in response.data
    assert response.data['is_blocked'] is True


def test_user_block_added(client, example_user, test_user, jwt_headers):
    """ Добавление в черный список другим пользователем. """
    assert not example_user.black_listed(test_user)
    response = client.post(
        reverse('v2:user-block', kwargs={'uuid': test_user.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert example_user.black_listed(test_user)


def test_user_block_removed(client, example_user, blocked_user, test_user, jwt_headers):
    """ Удаление пользователя из черного списка. """
    assert example_user.black_listed(test_user)
    response = client.delete(
        reverse('v2:user-block', kwargs={'uuid': test_user.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not example_user.black_listed(test_user)


def test_user_get_black_list(client, example_user, blocked_user, test_user, jwt_headers):
    """ Проверка черного списка пользователя. """
    response = client.get(reverse('v2:user-black-list'), **jwt_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count']
    assert response.data['count'] == \
        example_user.black_list.all().count()


def test_user_profiles_accessable(client, jwt_headers):
    """ Проверка доступности все пользовательских профилей. """
    other_uuid = None
    for u in get_user_model().objects.filter(is_active=True):
        response = client.get(
            reverse('v2:user-detail', kwargs={'uuid': other_uuid or u.uuid}),
            **jwt_headers
        )
        other_uuid = u.uuid
        assert response.status_code == status.HTTP_200_OK


def test_user_object_level_permissions(client, example_user, test_user, jwt_headers):
    """ Проверика доступов на уровне объектов. """
    response = client.patch(
        reverse('v2:user-detail', kwargs={'uuid': example_user.uuid}),
        json.dumps({'display_name': 'New name'}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK

    response = client.patch(
        reverse('v2:user-detail', kwargs={'uuid': test_user.uuid}),
        json.dumps({'display_name': 'New name'}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_user_who_is_near_nobody(client, example_user, test_user, jwt_headers):
    """ Рядом с собой никого нет (в формате FeatureCollection). """
    response = client.get(
        reverse('v2:user-who') + '?radius=100',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'features' in response.data
    assert 'type' in response.data
    assert 'count' not in response.data
    assert response.data['type'] == 'FeatureCollection'
    assert len(response.data['features']) == 0


@pytest.mark.skip(reason='Горячка. Жалоб не поступало.')
def test_user_who_is_near_locations(client, example_user, test_user, jwt_headers):
    """ Находим одного юзера в радиусе 250км. """
    response = client.get(
        reverse('v2:user-who') + '?radius=250000',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'features' in response.data
    assert 'type' in response.data
    assert response.data['type'] == 'FeatureCollection'
    assert len(response.data['features']) == 1


def test_user_who_is_near_nobody_that_age(client, example_user, test_user, jwt_headers):
    """ Ниодного пользователя указанного возраста. """
    response = client.get(
        reverse('v2:user-who') + '?radius=250000&sex=F&age=40-45',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'features' in response.data
    assert 'type' in response.data
    assert response.data['type'] == 'FeatureCollection'
    assert len(response.data['features']) == 0


def test_user_who_is_near_someone_that_age(client, example_user, test_user, jwt_headers):
    """ Один пользователь указанного пола. """
    response = client.get(
        reverse('v2:user-who') + '?radius=250000&sex=F',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'features' in response.data
    assert 'type' in response.data
    assert response.data['type'] == 'FeatureCollection'
    assert len(response.data['features']) == 0


def test_user_who_is_near_distance_bug(client, example_user, test_user, jwt_headers):
    """ Баг с попаданием пользователя из-за радиуса поиска. """
    # d.1 r=1.4 z=16.799625 fp=(55.5174824, 36.0430845) tp=(55.50385756888095, 36.04244764608467)
    example_user.location = Point(55.5174824, 36.0430845)
    example_user.is_online = True
    example_user.save()

    test_user.location = Point(55.50385756888095, 36.04244764608467)
    test_user.is_online = True
    test_user.save()

    response = client.get(
        reverse('v2:user-who') + '?radius=1400',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['features']) == 0


@pytest.mark.skip(reason='Горячка. Жалоб не поступало.')
def test_user_list_feature_collection(client, example_user, test_user, jwt_headers):
    """ FeatureCollection с пагинацией. """
    response = client.get(
        reverse('v2:user-who-list') + '?radius=250000',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'features' in response.data
    assert 'type' in response.data
    assert 'count' in response.data
    assert response.data['type'] == 'FeatureCollection'
    assert len(response.data['features']) == 1
