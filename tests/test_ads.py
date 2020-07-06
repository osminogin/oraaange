import json
from datetime import timedelta

from django.urls import reverse
from django.http import QueryDict
from django.utils import timezone
from rest_framework import status

from ads.models import Ad


def test_api_create_ad(client, jwt_headers):
    """ Создание нового объявления. """
    meeting_time = timezone.now() + timedelta(days=1)   # In future
    data = {
        'title': 'Example ad',
        'type': Ad.Type.dating,
        'address': 'ul. Mira, 8',
        'text': 'Ad text.',
        'ages': (18, 80),
        'period': (meeting_time.strftime('%s.%f'), None),
        # 'sex': 'M',
        'point': {
            'type': 'Point',
            'coordinates': [125.6, 10.1]
        }
    }
    response = client.post(
        reverse('v2:ad-list'),
        data=json.dumps(data),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert 'type' in response.data
    assert response.data['type'] == 'DATING'
    # В данный момент в AdSerializer отсутствует
    # assert 'geometry' in response.data
    # assert response.data['type'] == 'Feature'


def test_api_retrieve_ad(client, jwt_headers, example_ad):
    """ Получение информации о предложении. """
    response = client.get(
        reverse('v2:ad-detail', kwargs={'uuid': example_ad.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'type' in response.data
    assert response.data['type'] == 'DATING'
    # В данный момент в AdSerializer отсутствует
    # assert 'geometry' in response.data
    # assert response.data['type'] == 'Feature'


def test_api_update_ad(client, jwt_headers, example_ad):
    """ Обновление объявления """
    data = {
        'type': Ad.Type.dating,
        'ages': (18, None),
        'text': 'Ad text.',
        'sex': 'M',
        'point': {
            'type': 'Point',
            'coordinates': [125.6, 10.1]
        }
    }
    response = client.patch(
        reverse('v2:ad-detail', kwargs={'uuid': example_ad.uuid}),
        data=json.dumps(data),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK, response.data


def test_api_ad_retrieve_delete(client, jwt_headers, example_ad):
    """ Получение и удаление объявления """
    response = client.delete(
        reverse('v2:ad-detail', kwargs={'uuid': example_ad.uuid}),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_api_list_ads(client, jwt_headers, example_ad):
    """ Получение списка объявлений. """
    response = client.get(reverse('v2:ad-list'), **jwt_headers)
    assert response.status_code == status.HTTP_200_OK
    assert 'type' in response.data
    assert 'count' in response.data
    assert 'features' in response.data
    assert response.data['type'] == 'FeatureCollection'
    assert response.data['count'] == 1


def test_api_list_archive_ads(client, jwt_headers, example_ad):
    """ Список архивных объявлений (срок завершения мероприятия вышел). """
    q = QueryDict('', mutable=True)
    q['is_archive'] = True
    example_ad.period = [None, timezone.now() - timedelta(days=1)]
    example_ad.save()
    response = client.get(
        reverse('v2:ad-list') + f'?{q.urlencode()}',
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
