from django.contrib import admin
from django.db.models import Count, F, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from taggit.models import Tag

from abuses.models import AdAbuse

from .models import User

title = "Limon administration interface"
admin.site.site_title = title
admin.site.site_header = title
admin.site.index_title = title

admin.site.unregister(Tag)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'get_sex_display', 'birth_date',
        'confirm_tos', 'is_restricted',
        'in_userabuse', 'out_userabuse',
        'in_adabuse', 'out_adabuse'
    )
    readonly_fields = (
        'username', 'sex', 'birth_date',
        'confirm_tos',
        'in_userabuse', 'out_userabuse',
        'in_adabuse', 'out_adabuse'
    )
    list_filter = ('is_superuser', 'groups__name', 'confirm_tos', 'is_restricted')
    fieldsets = (
        (None, {
            'fields': (
                ('username', 'sex', 'birth_date'),
                ('confirm_tos', 'is_restricted'),
            )
        }),
        ('Meta', {
            'fields': (
                ('in_userabuse', 'out_userabuse'),
                ('in_adabuse', 'out_adabuse'),
            )
        })
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            in_userabuse=Count('userabuse', distinct=True),
            in_userabuse_confirmed=Count(
                'userabuse',
                filter=Q(userabuse__is_confirmed=True),
                distinct=True
            ),
            out_userabuse=Count('userabuses_sender', distinct=True),
            out_userabuse_confirmed=Count(
                'userabuses_sender',
                filter=Q(userabuses_sender__is_confirmed=True),
                distinct=True
            ),
            in_adabuse=Count(
                'ads',
                filter=Q(ads__id__in=AdAbuse.objects.filter(
                    ad__user_id=F('id')
                ).values('id')),
                distinct=True
            ),
            in_adabuse_confirmed=Count(
                'ads',
                filter=Q(ads__id__in=AdAbuse.objects.filter(
                    ad__user_id=F('id'), is_confirmed=True
                ).values('id')),
                distinct=True
            ),
            out_adabuse=Count('adabuses_sender', distinct=True),
            out_adabuse_confirmed=Count(
                'adabuses_sender',
                filter=Q(adabuses_sender__is_confirmed=True),
                distinct=True
            ),
        )
        return qs

    def _get_link(self, link_name, text, query):
        link = reverse(f'admin:{link_name}')
        output = f'<a href="{link}?{query}">{text}</a>'
        return mark_safe(output)

    def in_userabuse(self, obj):
        query = f'user__id__exact={obj.id}'
        value = f'{obj.in_userabuse} ({obj.in_userabuse_confirmed})'
        output = self._get_link(
            'abuses_userabuse_changelist', value, query
        )
        return output

    def out_userabuse(self, obj):
        query = f'sender__id__exact={obj.id}'
        value = f'{obj.out_userabuse} ({obj.out_userabuse_confirmed})'
        output = self._get_link(
            'abuses_userabuse_changelist', value, query
        )
        return output

    def in_adabuse(self, obj):
        query = f'sender__id__exact={obj.id}'
        value = f'{obj.in_adabuse} ({obj.in_adabuse_confirmed})'
        output = self._get_link(
            'abuses_adabuse_changelist', value, query
        )
        return output

    def out_adabuse(self, obj):
        query = f'sender__id__exact={obj.id}'
        value = f'{obj.out_adabuse} ({obj.out_adabuse_confirmed})'
        output = self._get_link(
            'abuses_adabuse_changelist', value, query
        )
        return output
