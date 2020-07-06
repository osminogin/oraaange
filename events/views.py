from rest_framework import mixins, viewsets

from .models import Event
from .serializers import EventSerializer


class EventViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """
    Event viewset.
    """
    lookup_field = 'uuid'
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
