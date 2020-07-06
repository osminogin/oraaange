import json

from django.urls import reverse
from rest_framework import status

from events.serializers import EventSerializer


def test_api_create_event(client, example_user, jwt_headers):
    """ Создание нового объявления. """
    data = {
        'payload': {
            'some': 'payload'
        },
        'recipients': [str(example_user.uuid)]
    }

    response = client.post(
        reverse('v2:event-list'),
        data=json.dumps(data),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Используем сериализатор для проверки данных
    serializer = EventSerializer(data=response.data)
    assert serializer.is_valid()
