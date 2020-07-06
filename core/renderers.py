import json

from rest_framework.renderers import JSONRenderer


class JSONDictRenderer(JSONRenderer):
    def render(self, *args, **kwargs):
        return json.loads(super().render(*args, **kwargs))
