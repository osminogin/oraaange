import os
import re
import random
import mimetypes
from math import cos, pi, pow

import jwt
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework.request import Request
from rest_framework_jwt.authentication import JSONWebTokenAuthentication


def gen_smscode():
    """ Генеация нового уникального кода для СМС. """
    return random.randint(0000, 9999)


def get_random_phone():
    """ Случайный номер телефона. """
    return str(random.randint(71000000000, 79999999999))


def get_jwt_payload(token):
    """ Получение сериализованного payload из JWT-токен. """
    return jwt.decode(token, settings.SECRET_KEY)


def get_user_jwt(request):
    """
    Replacement for django session auth get_user & auth.get_user
     JSON Web Token authentication. Inspects the token for the user_id,
     attempts to get that user from the DB & assigns the user on the
     request object. Otherwise it defaults to AnonymousUser.

    Returns: instance of user object or AnonymousUser object
    """
    user = None
    try:
        user_jwt = JSONWebTokenAuthentication().authenticate(Request(request))
        if user_jwt is not None:
            # store the first part from the tuple (user, obj)
            user = user_jwt[0]
    except:     # noqa
        pass

    return user or AnonymousUser()


def get_user_or_create(**kwargs):
    """ Создает или возращает существующего пользователя. """
    try:
        return get_user_model().objects.get(username=kwargs['username'])
    except ObjectDoesNotExist:
        return get_user_model().objects.create(**kwargs)


def get_client_ip(request):
    """ Возвращает IP-адрес клиента из джанговского request. """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_file_type(file_name):
    """ Определяет тип файла по имени. """
    file_type = ''

    mime_type = mimetypes.guess_type(file_name)[0]
    if mime_type:
        file_type = mime_type.split('/')[0]

    File = apps.get_model('files', 'File')  # noqa

    # Допустимые значения для типов файлов: image, video, audio и document
    return getattr(File.Type, file_type.upper(), File.Type.DOCUMENT)


def get_public_url(file_uuid, prefix=''):
    public_url = os.path.join(
        settings.AWS_S3_ENDPOINT_URL,
        settings.AWS_STORAGE_BUCKET_NAME,
        prefix,
        str(file_uuid)
    )
    return public_url


def get_best_minpoints_dbscan(points_count, minpoints=None):
    if not minpoints or minpoints > points_count:
        minpoints = points_count
    if not minpoints:
        if points_count > 3:
            minpoints = 2
        elif minpoints > 16:
            minpoints = 3
        elif minpoints > 36:
            minpoints = 4
    else:
        minpoints = 2
    return minpoints


def fix_rawsql_helper(sql):
    # XXX: Грязный воркараунд. Почему-то доставая сам сырой запрос из
    #      queryset параметры не заключаются в скобки или экранируются
    #      должным образом - приходится в ручную редактировать SQL-запрос.
    sql = re.sub(
        r' BETWEEN\s+([^\s]+)\s+AND\s+([^\s\)]+)',
        r" BETWEEN '\1' AND '\2'",
        sql
    )
    sql = re.sub(
        r' "(\w+)"."sex"\s+=\s+([MFN])',
        r' "\1"."sex" = ' + r"'\2'",
        sql
    )
    sql = re.sub(r'\[UUID\(', 'ARRAY[UUID(', sql)
    sql = re.sub(r'"users"."uuid" = ([^\s\)]+)', r'"users"."uuid" = ' + r"'\1'", sql)
    sql = re.sub(r' NumericRange', 'int4range', sql)
    return sql


def get_meter_per_pixel(zoom):
    meter_pixel = 156543.03392 * cos(54.65 * pi / 180) / pow(2, zoom)
    return meter_pixel


def get_new_messages_count(user):
    """ Количество непрочитанных сообщений для пользователя.

    XXX: Требует наблюдия и возможно оптимизации. """
    Message = apps.get_model('chats', 'Message')  # noqa
    unread_count = Message.objects \
        .filter(chat__in=user.chats) \
        .exclude(Q(sender=user) | Q(sender__in=user.black_list.all())) \
        .filter(status=Message.Status.new, deleted_at=None) \
        .count()
    return unread_count


def get_rows_from_cursor(cursor):
    """Returns all rows from a cursor as a dict"""
    desc = cursor.description
    return [dict(zip([c[0] for c in desc], r)) for r in cursor.fetchall()]
