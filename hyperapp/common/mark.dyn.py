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
            path=[*self._path, fn.__name__],
            )
        add_fn_module_constructor(fn, ctr)
        module = inspect.getmodule(fn)
        name = fn.__name__
        try:
            prev_fn = getattr(module, name)
        except AttributeError:
            pass
        else:
            # Parameter fixture with same name is already present, make duplicates.
            idx = 1
            while True:
                if not hasattr(module, f'{name}_{idx}'):
                    break
                idx += 1
            if idx == 1:
                # Save previous one.
                setattr(module, f'{name}_{idx}', prev_fn)
                idx += 1
            setattr(module, f'{name}_{idx}', fn)
        return fn


def global_command(fn):
    ctr = htypes.global_command_ctr.global_command_ctr()
    add_fn_module_constructor(fn, ctr)
    return fn


def mark():
    return SimpleNamespace(
        param=ParamMarker(),
        service=ServiceMarker(),
        global_command=global_command,
        )
