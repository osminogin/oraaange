class LimonBaseException(Exception):
    """ Базоое для всех наших исключений. """


class RemoteAPIError(LimonBaseException):
    """ Ошибка удаленного API. """
