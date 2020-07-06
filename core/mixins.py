from django.http import Http404


class NotFoundOnDeletedObjectMixin:

    def get_object(self):
        obj = super().get_object()
        if hasattr(obj, 'deleted_at') and obj.deleted_at is not None:
            raise Http404
        return obj
