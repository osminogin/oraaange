import re
import six

from django.core import validators
from django.utils.translation import gettext_lazy as _


class InternationNubmerValidator(validators.RegexValidator):
    """ Validate by E.164 standart. https://en.wikipedia.org/wiki/E.164 """
    regex = r'^[1-9]\d{1,14}$'
    message = _('Must be valid international phone number.')
    flags = re.UNICODE if six.PY2 else 0
