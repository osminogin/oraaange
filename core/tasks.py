import requests
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from celery import shared_task

from abuses.models import AdAbuse, UserAbuse
from ads.models import Ad


@shared_task
def notify_and_block_ad(abuse_ids):
    abuses = AdAbuse.objects.filter(id__in=abuse_ids)
    to_block_ad_ids = []
    for abuse in abuses:
        # send_mail(
        #     'Abuse on ad',
        #     'You have abuse on your ad',
        #     settings.DEFAULT_FROM_EMAIL,
        #     [abuse.ad.owner.email]
        # )
        if abuse.ad.abuses.filter(is_confirmed=True).count() > 3:
            to_block_ad_ids.append(abuse.ad.id)

    Ad.objects.filter(id__in=to_block_ad_ids).update(is_blocked=True)


@shared_task
def notify_and_block_user(abuse_ids):
    abuses = UserAbuse.objects.filter(id__in=abuse_ids)
    to_block_user_ids = []
    for abuse in abuses:
        # send_mail(
        #     'Abuse on you',
        #     'You have abuse on your profile',
        #     settings.DEFAULT_FROM_EMAIL,
        #     [abuse.user.email]
        # )
        if abuse.user.abuses.filter(is_confirmed=True).count() > 3:
            to_block_user_ids.append(abuse.user.id)

    get_user_model().objects.filter(
        id__in=to_block_user_ids
    ).update(is_blocked=True)


@shared_task
def send_sematext_metrics(metric, value, aggregation,
                          filter1=None, filter2=None):
    """
    Асинхронная отсылка метрики в Sematext.
    """
    assert aggregation in ('sum', 'avg', 'min', 'max')
    if not settings.SPM_APP_TOKEN:
        return
    req = {
        'datapoints': [
            {
                'timestamp': int(datetime.now().timestamp() * 1000),
                # XXX: Сука блять как достать __время постановки__ задания в очередь -
                #   тут будет время выполнение таска, что не совсем точно
                #   для сбора статистики.
                'name': metric,
                'value': float(value),
                'aggregation': aggregation,
            }
        ]
    }
    # XXX:
    if filter1:
        req['datapoints'][0]['filter1'] = filter1
    if filter2:
        req['datapoints'][0]['filter2'] = filter2

    r = requests.post(
        f'http://spm-receiver.eu.sematext.com/receiver/custom/receive.json?token={settings.SPM_APP_TOKEN}',
        json=req
    )
    r.raise_for_status()
    return True
