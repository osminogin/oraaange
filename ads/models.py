from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.contrib.postgres.fields import (
    ArrayField, DateTimeRangeField, IntegerRangeField
)
from django.template.defaultfilters import truncatewords
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from core.models import BaseModel
from core.managers import CustomManager


class AdManager(CustomManager):

    def get_queryset(self):
        return super().get_queryset().filter(is_blocked=False)


def default_period():
    return timezone.now(), None


class Ad(BaseModel):
    """
    Ads model.
    """
    class Type:
        dating = 'DATING'
        meeting = 'MEETING'
        travel = 'TRAVEL'
        choices = (
            (dating, _('Dating')),
            (meeting, _('Meeting')),
            (travel, _('Travel')),
        )

    user = models.ForeignKey(
        get_user_model(),
        related_name='ads',
        on_delete=models.CASCADE,
        help_text=_('Ad creator.')
    )
    type = models.CharField(
        max_length=16, choices=Type.choices, help_text=_('Ad type.')
    )
    address = models.CharField(
        max_length=256,
        help_text=_('Ad address.')
    )
    point = models.PointField(
        help_text=_('Geolocation point (in GeoJSON format).')
    )
    sex = models.CharField(
        max_length=1,
        choices=get_user_model().Sex.choices,
        default=get_user_model().Sex.none,
        help_text=_('Valid values: M, F, N')
    )
    ages = IntegerRangeField(help_text=_('Ad age range'))
    title = models.CharField(max_length=128, help_text=_('Title'))
    text = models.TextField(help_text=_('Ad description'))
    period = DateTimeRangeField(
        default=default_period, help_text=_('Ad period')
    )
    favorited_for = ArrayField(
        models.CharField(max_length=36),
        help_text=_("Favorite for this users (list of UUIDs)."),
        default=list
    )
    viewed_by = ArrayField(
        models.CharField(max_length=36),
        help_text=_("View by this users (list of UUIDs)."),
        default=list
    )
    is_active = models.BooleanField(
        default=False, help_text=_('As is publicly published.')
    )
    is_blocked = models.BooleanField(
        default=False, help_text=_('Is blocked by moderator')
    )

    objects = AdManager()

    class Meta:
        db_table = 'ads'
        ordering = ('-created_at',)

    @cached_property
    def owner(self):
        return self.user

    @property
    def short_text(self):
        return truncatewords(self.text, 6)
