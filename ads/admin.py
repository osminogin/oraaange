from django.contrib import admin
from .models import Ad
from core.admin import UserLinkMixin


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin, UserLinkMixin):
    date_hierarchy = 'created_at'
    list_display = (
        'short_text', 'user_link', 'sex', 'point', 'is_active', 'created_at'
    )
    readonly_fields = (
        'text', 'user_link', 'sex', 'point', 'is_active', 'created_at'
    )
    list_filter = ('sex', 'is_active')
    fieldsets = (
        (None, {
            'fields': ('text', )
        }),
        ('Meta', {
            'fields': (
                ('user_link', 'sex', 'is_active', 'created_at'),
                'point'
            )
        })
    )

    def user_link(self, obj):
        return self._get_user_link(obj.user)
