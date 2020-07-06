from datetime import datetime
from calendar import timegm
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.utils import get_username, get_username_field

from users.serializers import UserSerializer


def custom_jwt_payload_handler(user):
    username_field = get_username_field()
    username = get_username(user)

    payload = {
        'user_id': user.pk,
        'username': username,
        'user_uuid': str(user.uuid),
        'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
        username_field: username
    }

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload


def custom_jwt_response_handler(token, user=None, request=None):
    """ Returns the response data for both the login and refresh views. """
    data = {
        'token': token
    }
    if user and user.is_new_user:
        data['new_user'] = True
    data['user'] = UserSerializer(
        user,
        context={'request': request}).data
    return data
