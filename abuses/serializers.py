from rest_framework import serializers

from .models import AdAbuse, UserAbuse


class UserAbuseSerializer(serializers.ModelSerializer):
    """
    Сериализатор жалобы на пользователя.
    """
    user = serializers.SlugRelatedField(slug_field='uuid', read_only=True)

    class Meta:
        model = UserAbuse
        fields = ('reason', 'comment', 'user')


class AdAbuseSerializer(serializers.ModelSerializer):
    """
    Сериализатор жалобы на объявление.
    """
    ad = serializers.SlugRelatedField(slug_field='uuid', read_only=True)

    class Meta:
        model = AdAbuse
        fields = ('reason', 'comment', 'ad')
