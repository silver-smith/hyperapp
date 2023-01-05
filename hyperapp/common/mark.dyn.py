import inspect
from types import SimpleNamespace

from . import htypes
from .services import (
    mosaic,
    )
from .code.constants import RESOURCE_CTR_ATTR


def add_fn_module_constructor(fn, ctr):
    module = inspect.getmodule(fn)
    ctr_dict = module.__dict__.setdefault(RESOURCE_CTR_ATTR, {})
    ctr_list = ctr_dict.setdefault(fn.__name__, [])
    ctr_list.append(mosaic.put(ctr))


class ServiceMarker:

    def __call__(self, fn):
        ctr = htypes.attr_constructors.service(
            attr_name=fn.__name__,
            name=fn.__name__,
            )
        add_fn_module_constructor(fn, ctr)
        return fn


class ParamMarker:

    def __init__(self, path=None):
        self._path = path or []

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return ParamMarker([*self._path, name])

    def __call__(self, fn):
        ctr = htypes.attr_constructors.parameter(
            attr_name=fn.__name__,
            path=[*self._path, fn.__name__],
            )
        add_fn_module_constructor(fn, ctr)
        return fn


class ModuleMarker:

    def __init__(self, path=None):
        self._path = path or []

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return ModuleMarker([*self._path, name])

    def __call__(self, fn):
        return fn


def mark():
    return SimpleNamespace(
        param=ParamMarker(),
        service=ServiceMarker(),
        module=ModuleMarker(),
        )
