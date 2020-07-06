from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from taggit.managers import TaggableManager

from core.models import BaseModel
from core.utils import gen_smscode, get_public_url

from .validators import InternationNubmerValidator


class SMSCode(models.Model):
    """
    Модель для СМС-кодов.
    """
    code = models.CharField(
        max_length=4, validators=[MinLengthValidator(4)], editable=False,
        default=gen_smscode, help_text=_('Code from SMS.'),
    )
    sended = models.DateTimeField(
        auto_now_add=True, help_text=_('SMS sending time.')
    )

    def __str__(self):
        return str(self.code)


class User(AbstractUser, BaseModel):
    """
    User model.
    """
    class Sex:
        male = 'M'
        female = 'F'
        none = 'N'

        choices = (
            (male, _('Male')),
            (female, _('Female')),
            (none, _('None')),
        )

    username_validator = InternationNubmerValidator()
    username = models.CharField(
        _('username'),
        max_length=15,
        unique=True,
        help_text=_('Required. 15 characters or fewer. '
                    'Validated by ITU-T recommendation (E.164).'),
        validators=[username_validator],
        error_messages={
            'unique': _('A user with that username already exists.'),
        },
    )

    first_name = None
    last_name = None
    created_at = property(lambda x: x.date_joined)
    date_joined = models.DateTimeField(
        _('date joined'),
        default=timezone.now,
        db_column='created_at'
    )
    display_name = models.CharField(
        max_length=32, blank=True, help_text=_('Display name.')
    )
    avatar_uuid = models.UUIDField(blank=True, null=True)
    device_id = models.CharField(max_length=180, blank=True, null=True)
    sex = models.CharField(
        max_length=1, choices=Sex.choices,  # default=Sex.none,
        help_text='Valid Values: M or F'
    )
    location = models.PointField(
        blank=True, null=True, help_text='Last user location.'
    )
    birth_date = models.DateField(
        null=True, default=None, help_text=_('Birtht date.')
    )
    sms_code = models.OneToOneField(
        SMSCode, null=True, on_delete=models.CASCADE, related_name='sms_code'
    )
    confirm_tos = models.BooleanField(
        default=False, help_text='User confirm the offer.'
    )
    last_activity = models.DateTimeField(
        blank=True, null=True, help_text='Last user activity'
    )
    show_activity = models.BooleanField(
        default=True, help_text='Show user ativity to others'
    )
    is_restricted = models.BooleanField(
        default=False, help_text='User is blocked.'
    )
    is_online = models.BooleanField(default=False, help_text='Is user online')

    black_list = models.ManyToManyField('self', blank=True, symmetrical=False)

    interests = TaggableManager(verbose_name='interests')

    class Meta:
        db_table = 'users'

    @cached_property
    def owner(self):
        return self

    @property
    def phone(self):
        return str(self.username)

    @property
    def is_new_user(self):
        """ Новый требующий дополнительные шаги для заполнения профиля. """
        return not self.confirm_tos

    def delete(self, *args, **kwargs):
        """ Не удаляем пользователей. """
        self.deleted_at = timezone.now()
        self.save()

    def black_listed(self, user):
        """ Пользователь входит в черный список. """
        return self.black_list.filter(pk=user.pk).exists()

    def get_avatar_url(self):
        if self.avatar_uuid:
            return get_public_url(self.avatar_uuid, prefix='av')
