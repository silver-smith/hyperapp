import inspect
from types import SimpleNamespace

from . import htypes
from .services import (
    mosaic,
    )
from .code.constants import RESOURCE_CTR_ATTR


class Marker:

    def __init__(self, name):
        self._name = name

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return Marker(f'{self._name}.{name}')

    def __call__(self, fn):
        module = inspect.getmodule(fn)
        ctr_dict = module.__dict__.setdefault(RESOURCE_CTR_ATTR, {})
        ctr_list = ctr_dict.setdefault(fn.__name__, [])
        ctr = htypes.attr_constructors.service(name=fn.__name__)
        ctr_list.append(mosaic.put(ctr))
        return fn


def mark():
    return SimpleNamespace(
        param=Marker('param'),
        service=Marker('service'),
        )
