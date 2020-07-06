from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from core import tasks
from core.admin import UserLinkMixin

from .models import AdAbuse, UserAbuse


class AbuseAdmin(admin.ModelAdmin, UserLinkMixin):
    date_hierarchy = 'created_at'
    actions = ['confirm', 'reject']

    def sender_link(self, obj):
        return self._get_user_link(obj.sender)

    def confirm(self, request, queryset):
        queryset.update(is_confirmed=True)
        model = self.model.__name__.lower()
        abuse_ids = queryset.values_list('id', flat=True)
        getattr(tasks, f'notify_and_block_{model}').delay(abuse_ids)

    confirm.short_description = "Mark selected abuses as confirmed"

    def reject(self, request, queryset):
        queryset.update(is_confirmed=False)

    reject.short_description = "Mark selected abuses as rejected"


@admin.register(UserAbuse)
class UserAbuseAdmin(AbuseAdmin):
    list_display = (
        'reason', 'user_link', 'sender_link', 'short_comment',
        'is_confirmed', 'created_at'
    )
    readonly_fields = (
        'user_link', 'reason', 'comment', 'sender_link', 'created_at', 'updated_at'
    )
    list_select_related = ('user', 'sender')
    list_filter = ('reason', 'is_confirmed')
    fieldsets = (
        (None, {
            'fields': (
                ('user_link', 'reason'),
                'comment'
            )
        }),
        ('Meta', {
            'fields': (
                ('sender_link', 'is_confirmed'),
                ('created_at', 'updated_at')
            )
        })
    )

    def user_link(self, obj):
        return self._get_user_link(obj.user)


@admin.register(AdAbuse)
class AdAbuseAdmin(AbuseAdmin):
    list_display = (
        'reason', 'ad_link', 'sender_link', 'short_comment',
        'is_confirmed', 'created_at'
    )
    readonly_fields = (
        'ad_link', 'reason', 'comment', 'sender_link', 'created_at', 'updated_at'
    )
    list_select_related = ('ad', 'sender')
    list_filter = ('reason', 'is_confirmed')
    fieldsets = (
        (None, {
            'fields': (
                ('ad_link', 'reason'),
                'comment'
            )
        }),
        ('Meta', {
            'fields': (
                ('sender_link', 'is_confirmed'),
                ('created_at', 'updated_at')
            )
        })
    )

    @staticmethod
    def ad_link(obj):
        link = reverse('admin:ads_ad_change', args=[obj.ad.id])
        output = f'<a href="{link}">{obj.ad.user.username}</a>'
        return mark_safe(output)
