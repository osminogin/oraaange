import uuid

from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model.
    """
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text='UUID of object.'
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        editable=False
    )
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        abstract = True
        ordering = ('created_at',)
