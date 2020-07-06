from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models import BaseModel


class Event(BaseModel):
    """
    Event model.
    """
    updated_at = None
    deleted_at = None

    payload = JSONField(help_text=_('Event data.'))
    recipients = ArrayField(
        # TODO: try ForeignKey
        models.CharField(max_length=36),
        default=list,
        help_text=_('Event recipients (list of UUIDs).')
    )
    sender = models.ForeignKey(
        get_user_model(),
        help_text=_('Event sender.'),
        blank=True, null=True, on_delete=models.SET_NULL
    )
    delivered_to = ArrayField(
        models.CharField(max_length=36),
        default=list,
        help_text=_('Event delivered to recipients (list of UUIDs).')
    )
