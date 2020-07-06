import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.serializers import EmptySerializer
from core.permissions import OnlyOwnerAllowedEdit
from .serializers import (
    ContactSerializer, ContactImportSerializer, ContactUpdateSerializer
)
from .filters import ContactFilter
from .models import Contact


class ContactViewSet(mixins.ListModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """
    A viewset for personal contact list manipulation.

    destroy:
        Удаляет пользователя из списка контактов по его UUID.
    """
    lookup_field = 'user__uuid'
    lookup_url_kwarg = 'uuid'
    queryset = Contact.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ContactFilter
    permission_classes = (IsAuthenticated, OnlyOwnerAllowedEdit,)
    http_method_names = ('post', 'patch', 'get', 'delete',)

    def get_serializer_class(self):
        """
        Различные методы используют различные сериализаторы.
        """
        if self.action == 'importing':
            return ContactImportSerializer
        elif self.action in ('update', 'partial_update',):
            return ContactUpdateSerializer
        else:
            return ContactSerializer

    def get_queryset(self):
        """
        Контакты фильтруютися по текущему пользоавтелю.
        Заблокированных выбрасываем.
        """
        return super().get_queryset().filter(holder=self.request.user.pk)

    def update(self, request, *args, **kwargs):
        """ Автоматически создаем контакты при попытке апдейта. """
        try:
            self.get_object()
        except Http404:
            user = get_object_or_404(get_user_model(), uuid=kwargs['uuid'])
            request.user.contacts.create(user=user)

        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: 'Contact-list successfully imported.',
            413: 'Should be no more than 100 contacts in one request.'
        }
    )
    @action(methods=['post'], detail=False, url_path=r'import', url_name='import')
    def importing(self, request, *args, **kwargs):
        """
        Поиск номеров зарегистрированных пользователей.
        Возвращает список объектов User.
        """
        serializer = self.get_serializer(
            data=request.data,
            many=True if isinstance(request.data, list) else False
        )
        serializer.is_valid(raise_exception=True)

        # Ограничение размера запроса
        if len(serializer.data) > settings.REST_FRAMEWORK['PAGE_SIZE']:
            return Response(status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # Берем список зарегистрированых юзеров из запроса ...
        users = get_user_model().objects.filter(
            username__in=[u['phone'] for u in serializer.data['contacts']]
        )

        # ... и пихаем всех найденых в свои контакты
        Contact.objects.bulk_create([
            Contact(holder=request.user, user=contact) for contact in users
        ])

        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=EmptySerializer,
        responses={
            201: 'User added to contact list.',
            404: 'User don\'t exists.',
        }
    )
    @action(methods=['post'], detail=True)
    def add(self, request, *args, **kwargs):
        """ Добавляет зарегистрированного пользователя в контакт-лист. """
        try:
            uuid.UUID(kwargs.get('uuid'))
            assert Contact.objects.create(
                holder=request.user,
                user=get_user_model().objects.get(uuid=kwargs['uuid']),
                is_from_app=True
            )
        except (IntegrityError, ValueError, AssertionError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_201_CREATED)
