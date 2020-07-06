import requests
from uuid import UUID
from celery import shared_task
from celery.utils.log import get_task_logger

from django.conf import settings
from core.exceptions import RemoteAPIError
from core.tasks import send_sematext_metrics

logger = get_task_logger(__name__)


@shared_task
def send_sms_code(phone, code):
    """
    Отправлка СМС-код на номер получателя.
    """
    if not settings.SMSRU_ENABLED:
        logger.warning('SMS.ru service disabled in settings')
        return

    # XXX: Split
    traget_url = f'https://sms.ru/sms/send?api_id={settings.SMSRU_API_KEY}' \
                 f'&to[{phone}]=Code+{code}&json=1'
    response = requests.get(traget_url)
    data = response.json()
    if data['status'] != 'OK':
        raise RemoteAPIError(data['status_text'])

    # Проверка минимального баланса с выводом в лог
    min_balance = 100.0
    if data['balance'] < min_balance:
        logger.warning(
            f'Balance on SMS gateway is under {min_balance}'
            f' now {data["balance"]} rub'
        )

    # Отсылка метрики в Sematext
    if settings.SPM_APP_TOKEN:
        try:
            UUID(settings.SPM_APP_TOKEN, version=4)
            send_sematext_metrics('sms-auth-sended', value=1.0, aggregation='sum')
        except ValueError:
            pass

    return data['status']
