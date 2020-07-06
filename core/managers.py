from django.db import models


class CustomManager(models.Manager):

    def is_deleted(self):
        return self.filter(deleted_at__isnull=False)
