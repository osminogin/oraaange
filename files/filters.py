import django_filters

from .models import File


class FileFilter(django_filters.rest_framework.FilterSet):

    class Meta:
        model = File
        fields = {
            'file_type': ['iexact', ],
        }
