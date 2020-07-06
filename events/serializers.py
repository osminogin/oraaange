from rest_framework import serializers

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    """
    Events serializer.
    """
    sender = serializers.SlugRelatedField(slug_field='uuid', read_only=True)

    class Meta:
        model = Event
        fields = ('uuid', 'payload', 'recipients', 'created_at', 'sender',)
        read_only_fields = ('uuid', 'created_at',)
