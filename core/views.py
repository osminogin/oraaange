from django.http.response import HttpResponse


def ping(request):
    """ Ping-pong monitoring. """
    return HttpResponse('pong')
