import json

from django.urls import reverse
from rest_framework import status

from locations.serializers import DetectCountryByIPSerializer


def test_api_create_location(client, geojson_point, jwt_headers):
    """ Создание локации пользвателя. """
    response = client.post(
        reverse('v2:location-list'),
        json.dumps(geojson_point),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data is None


def test_api_detect_country_by_ip(client):
    """ Определение страны пользователя по IP. """
    response = client.get(
        reverse('v2:location-detect'),
        REMOTE_ADDR='194.67.22.11'  # Русский IP - где-то в недрах билайна
    )
    assert response.status_code == status.HTTP_200_OK
    serializer = DetectCountryByIPSerializer(data=response.json())
    assert serializer.is_valid()
