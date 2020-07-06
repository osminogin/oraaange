from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from users.serializers import UserSerializer


def validate_toggle_field(request, instance, data, field_name):
    sender = request.user
    is_update = request.method == 'PATCH'
    if instance:
        is_owner = sender == instance.owner
    else:
        is_owner = False

    toggle_field = data.get(field_name, None)
    if not is_owner and is_update and toggle_field is None:
        raise ValidationError('You can\'t update these fields')
    elif not is_owner and is_update and not (toggle_field is None):
        data = {field_name: toggle_field}

    return data


class EmptySerializer(serializers.Serializer):
    """ Пустой сеариализатор.

    Не нашел другого способа в автодоке отобразить пустой POST запросе.
    """


class UUIDSerializer(serializers.Serializer):
    """
    Сериализатор 1 поля UUID - используется в Create mixins.
    """
    uuid = serializers.UUIDField()


class TokenSerializer(serializers.Serializer):
    """
    Сериализатор ответа с токеном.
    """
    token = serializers.CharField()
    new_user = serializers.BooleanField(required=False, default=False)
    user = UserSerializer()
