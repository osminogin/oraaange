import django_filters

from .models import Contact


class ContactFilter(django_filters.rest_framework.FilterSet):

    class Meta:
        model = Contact
        fields = ['is_favorite', 'is_from_app']
