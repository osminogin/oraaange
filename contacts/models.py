from django import forms
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class Contact(BaseModel):
    """
    Модель списка контак-листа для пользователя.
    """
    uuid = None     # Потому что нахуй не нужно
    holder = models.ForeignKey(
        get_user_model(),
        related_name='contacts',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        help_text=_('User model.')
    )
    is_favorite = models.BooleanField(
        default=False,
        help_text='Flag for favorite contact.'
    )
    is_from_app = models.BooleanField(
        default=False,
        help_text='Contact added from application.'
    )

    class Meta:
        unique_together = ('holder', 'user',)
        ordering = ('is_favorite', 'updated_at',)

    def __str__(self):
        return f'{self.user} contact of {self.holder}'

    def __repr__(self):
        return f'{self.holder} - {self.user}'

    @cached_property
    def owner(self):
        return self.holder

    def clean(self):
        """ Валидация модели целиком. """
        if self.cleaned_data['user'] == self.cleaned_data['contact']:
            raise forms.ValidationError(
                'The user can\'t add himself to the contact list.'
            )
        return self.cleaned_data
