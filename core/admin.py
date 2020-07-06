from django.utils.safestring import mark_safe
from django.urls import reverse


class UserLinkMixin:

    def _get_user_link(self, user):
        link = reverse('admin:users_user_change', args=[user.id])
        output = f'<a href="{link}">{user.username}</a>'
        return mark_safe(output)
