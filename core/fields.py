from datetime import datetime

from rest_framework import serializers


class TimestampField(serializers.Field):
    """
    Timestamp field.
    """

    def to_internal_value(self, value):
        return datetime.fromtimestamp(int(value))

    def to_representation(self, value):
        if value:
            value = value.strftime('%s')
        return value


class TimestampRangeField(serializers.Field):
    """
    Timestamp range field.
    """

    def to_internal_value(self, value):
        begin, end = value
        begin = datetime.fromtimestamp(int(float(begin))) if begin else begin
        end = datetime.fromtimestamp(int(float(end))) if end else end
        return [begin, end]

    def to_representation(self, value):
        if isinstance(value, (list, tuple)):
            begin, end = value
        else:
            begin = value.lower
            end = value.upper

        begin = begin.strftime('%s') if begin else begin
        end = end.strftime('%s') if end else end
        value = [begin, end]
        return value


class ArrayToggleField(serializers.BooleanField):
    """
    Добавляет пользователя в список, если на входе True, и
    исключает из списка, если на входе False.
    Возвращает True, если пользователь в списке, и False,
    если пользователь не в списке.
    """
    def to_internal_value(self, value):
        value = super().to_internal_value(value)
        instance = self.parent.instance
        if not instance:
            return None

        source = getattr(instance, self.source, None)
        if not source and not value:
            return None

        user_uuid = str(self.parent.context['request'].user.uuid)
        if not source and value:
            return [user_uuid]

        if source and not value:
            source.pop(source.index(user_uuid))
            return source

        if source and value and user_uuid not in source:
            source.append(user_uuid)
            return source

        return source

    def to_representation(self, value):
        user_uuid = str(self.parent.context['request'].user.uuid)
        return user_uuid in value
