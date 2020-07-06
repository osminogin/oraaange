from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import RefreshJSONWebToken

from ads.views import AdViewSet
from contacts.views import ContactViewSet
from core.views import ping
from events.views import EventViewSet
from files.views import FileViewSet, minio_webhook
from locations.views import LocationViewSet
from users.views import InitialViewSet, ObtainJSONWebToken, UserViewSet

# Schema and API docs
schema_view = get_schema_view(
    openapi.Info(
        title='Oraaange API',
        default_version='v2',
        contact=openapi.Contact(email="osintsev@gmail.com"),
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

docs_view = include_docs_urls(
    permission_classes=(permissions.AllowAny,)
)


# Default router
router = DefaultRouter()
router.register(r'ads', AdViewSet)
router.register(r'events', EventViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'locations', LocationViewSet, basename='location')
# XXX: order mater
router.register(r'init', InitialViewSet, basename='initial')
router.register(r'users', UserViewSet)
router.register(r'files', FileViewSet)


# Urlpattern
urlpatterns = [

    url(r'^$', RedirectView.as_view(url=reverse_lazy('schema-swagger-ui'))),
    url(r'^ping/$', ping, name='ping'),
    url(r'^docs/', docs_view),

    # OpenAPI schema & docs
    url(r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'),
    url(r'^swagger/$',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'),
    url(r'^redoc/$',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'),

    # API v2
    url(r'^v2/', include((router.urls, 'v2'), namespace='v2')),
    url(r'^v2/login/$', ObtainJSONWebToken.as_view(), name='login'),
    url(r'^v2/refresh_token/$', RefreshJSONWebToken.as_view(), name='refresh_token'),
    url(r'^v2/files/webhook$', minio_webhook, name='file-webhook'),

    # Control panel
    url(r'^admin/', admin.site.urls),
]

# Debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
