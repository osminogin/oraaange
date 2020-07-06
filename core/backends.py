from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model


class SMSCodeUserBackend(object):
    """
    Авторизация пользователя по подку из SMS.
    Время жизни токена по ТЗ - 5 мин.
    Использует настройку окружения SMS_CODE_LIFETIME (время в секундах).
    """

    def authenticate(self, request, username=None, password=None):
        try:
            user = get_user_model()._default_manager.get_by_natural_key(username)
        except get_user_model().DoesNotExist:
            return

        # XXX: Hardcode for super code (need remove on production)
        if user.username == username and password == '1111':
            return user

        # Авторизует только по НЕ просроченному СМС-коду
        if getattr(user, 'sms_code', None):
            elapsed = timezone.now() - user.sms_code.sended
            if user.username == username and \
                    user.sms_code.code == password and \
                    elapsed < timedelta(seconds=settings.SMS_CODE_LIFETIME):
                return user
