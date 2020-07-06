import json

from django.urls import reverse
from rest_framework import status

from abuses.models import UserAbuse, AdAbuse


def test_api_create_user_abuse(client, jwt_headers, example_user):
    """ Создание жалобы на пользователя. """
    data = {
        "reason": UserAbuse.Reason.spam,
    }
    response = client.post(
        reverse('v2:user-abuse', kwargs={'uuid': str(example_user.uuid)}),
        data=json.dumps(data),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_api_create_ad_abuse(client, jwt_headers, example_ad):
    """ Создание жалобы на объявление. """
    data = {
        "reason": AdAbuse.Reason.advertising,
    }
    response = client.post(
        reverse('v2:ad-abuse', kwargs={'uuid': str(example_ad.uuid)}),
        data=json.dumps(data),
        **jwt_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
