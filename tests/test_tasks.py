import pytest
from users.tasks import send_sms_code
from core.tasks import send_sematext_metrics


@pytest.mark.webtest
def test_send_sms_code(request):
    """ Проверка таска отправки смс-кода. """
    result = send_sms_code.delay(request.config.test_username, '9999')
    assert result.ready()
    assert result.successful()


@pytest.mark.webtest
def test_send_sematext_metrics(client):
    result = send_sematext_metrics.delay('django-test', value=666, aggregation='avg')
    assert result.ready()
    assert result.successful()
