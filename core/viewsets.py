from rest_framework import mixins, viewsets

from core.mixins import NotFoundOnDeletedObjectMixin


class CustomModelViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet,
                         NotFoundOnDeletedObjectMixin):
    """
    Кастомный ModelViewSet, который включает дополнительные миксины.
    """
