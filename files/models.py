from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from core.managers import CustomManager
from core.models import BaseModel


class FileManager(CustomManager):

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at=None)

    def is_uploaded(self):
        return self.filter(is_uploaded=True)


def rename_to_uuid(instance, filename):
    """ Renames the file name to its UUID. """
    return str(instance.uuid)


class File(BaseModel):
    """
    File model.
    """
    class Type:
        IMAGE = 'image'
        VIDEO = 'video'
        AUDIO = 'audio'
        SPEECH = 'speech'
        DOCUMENT = 'document'
        PORTFOLIO = 'portfolio'
        AVATAR = 'avatar'
        SCREENSHOT = 'screenshot'

        choices = (
            (IMAGE, _('Image')),
            (VIDEO, _('Video')),
            (AUDIO, _('Audio')),
            (SPEECH, _('Speech')),
            (DOCUMENT, _('Document')),
            (PORTFOLIO, _('Portfolio')),
            (AVATAR, _('Avatar')),
            (SCREENSHOT, _('Screenshot')),
        )

    class Handler:
        NONE = 'none'
        AVATAR = 'avatar'
        AUDIO_ENCODING = 'audio_enc'
        VIDEO_ENCODING = 'video_enc'

        choices = (
            (NONE, _('None')),
            (AVATAR, _('Avatar')),
            (AUDIO_ENCODING, _('Audio Encoding')),
            (VIDEO_ENCODING, _('Video Encoding')),
        )

    user = models.ForeignKey(
        get_user_model(),
        related_name='files',
        null=True,
        on_delete=models.PROTECT
    )
    file = models.FileField(
        upload_to=rename_to_uuid,
        help_text='File object.',
        null=True
    )
    orig_name = models.CharField(max_length=64, help_text='Original file name.')
    file_type = models.CharField(
        max_length=9,
        choices=Type.choices,
        default=Type.DOCUMENT,
        help_text=_('Valid values: image, video, audio and document.')
    )
    file_size = models.PositiveIntegerField(null=True)
    mime_type = models.CharField(
        max_length=256,
        default='application/octet-stream',
        null=True
    )
    handler = models.CharField(
        max_length=9,
        choices=Handler.choices,
        default=None,
        null=True,
    )
    is_private = models.BooleanField(default=False)
    is_uploaded = models.BooleanField(default=False)
    is_compressed = models.BooleanField(default=False)
    metadata = HStoreField(null=True)

    objects = FileManager()

    class Meta:
        db_table = 'files'

    @cached_property
    def owner(self):
        return self.user
