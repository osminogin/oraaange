from django.contrib.gis.db import models
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property
from django.template.defaultfilters import truncatewords
from django.utils.translation import gettext_lazy as _
from core import models as core_models
from ads import models as ad_models


class BaseAbuse(core_models.BaseModel):
    """
    Base abuse model.
    """
    comment = models.CharField(
        max_length=1024, blank=True, null=True, help_text=_('Abuse comment')
    )
    sender = models.ForeignKey(
        get_user_model(),
        related_name='%(model_name)ss_sender',
        on_delete=models.CASCADE,
        help_text=_('Abuse sender')
    )
    is_confirmed = models.NullBooleanField(help_text=_('Is abuse confirmed'))

    @cached_property
    def owner(self):
        return self.sender

    class Meta:
        abstract = True

    def short_comment(self):
        if self.comment:
            return truncatewords(self.comment, 6)


class UserAbuse(BaseAbuse):
    """
    Abuse on user model.
    """
    class Reason:
        spam = 'SPAM'
        bad_behavior = 'BAD_BEHAVIOR'
        fraud = 'FRAUD'
        uncensored_content = 'UNCENSORED_CONTENT'

        choices = (
            (spam, _('Spam')),
            (bad_behavior, _('Bad behavior')),
            (fraud, _('Fraud')),
            (uncensored_content, _('Uncensored content'))
        )

    reason = models.CharField(
        max_length=32, choices=Reason.choices, help_text=_('Abuse reason')
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, help_text=_('On user')
    )

    class Meta:
        db_table = 'user_abuses'

    @cached_property
    def owner(self):
        return self.sender

    def __str__(self):
        return f'{self.user.username}: {self.reason}'


class AdAbuse(BaseAbuse):
    """
    Abuse on ad model.
    """
    class Reason:
        advertising = 'ADVERTISING'
        uncensored_content = 'UNCENSORED_CONTENT'

        choices = (
            (advertising, _('Advertising')),
            (uncensored_content, _('Uncensored content'))
        )

    reason = models.CharField(
        max_length=32, choices=Reason.choices, help_text=_('Abuse reason')
    )
    ad = models.ForeignKey(
        ad_models.Ad, on_delete=models.CASCADE, help_text=_('On ad')
    )

    class Meta:
        db_table = 'ad_abuses'

    @cached_property
    def owner(self):
        return self.sender

    def __str__(self):
        return f'{self.ad.uuid}: {self.reason}'
