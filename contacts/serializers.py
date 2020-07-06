from rest_framework import serializers

from users.serializers import UserSerializer, InitialSerializer

from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    """
    Contact serializator.
    """
    user = UserSerializer()

    class Meta:
        model = Contact
        fields = ('user', 'is_favorite',)


class ContactImportSerializer(serializers.Serializer):
    """
    Contact importing serializer.
    """
    contacts = InitialSerializer(many=True)


class ContactUpdateSerializer(serializers.ModelSerializer):
    """
    Serialzer for contact updating.
    """
    class Meta:
        model = Contact
        fields = ('is_favorite',)
