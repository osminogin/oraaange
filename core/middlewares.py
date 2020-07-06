from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from .utils import get_user_jwt


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware for authenticating JSON Web Tokens in Authorize Header.
    """
    def process_request(self, request):
        request.user = SimpleLazyObject(lambda: get_user_jwt(request))


class RestrictBlockedUsersMiddleware(MiddlewareMixin):
    """
    Отсекает запросы от заблокированных пользвателей с кодом - 423 Locked.
    """
    def process_request(self, request):
        if hasattr(request, 'user') and \
                request.user.is_authenticated and \
                request.user.is_restricted:
            return HttpResponse(status=423)  # Locked


class RestrictUsersWithoutLocationMiddleware(MiddlewareMixin):
    """
    Отсекает запросы от пользователей без локации.
    """
    def process_request(self, request):
        method = request.method

        if request.user.is_anonymous:
            return None

        # Пропускаем запросы методам регистрации и обновления локации
        if method == 'PATCH' and request.path.startswith('/v2/users/') or \
                method == 'POST' and request.path == '/v2/locations/':
            return None

        # Зарегистрированные пользователи без локации получают 424
        if hasattr(request.user, 'location') and \
                not request.user.location:
            return HttpResponse(status=424)  # Failed Dependency
