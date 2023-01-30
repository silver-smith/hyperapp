import inspect
from types import SimpleNamespace

from . import htypes
from .services import (
    mosaic,
    )
from .code.constants import RESOURCE_CTR_ATTR


def _copy_constructors(module, source_name, target_name):
    ctr_dict = module.__dict__.setdefault(RESOURCE_CTR_ATTR, {})
    source_ctr_list = ctr_dict.setdefault(source_name, [])
    target_ctr_list = ctr_dict.setdefault(target_name, [])
    target_ctr_list += source_ctr_list


def _add_constructor(module, fn_name, ctr):
    ctr_dict = module.__dict__.setdefault(RESOURCE_CTR_ATTR, {})
    ctr_list = ctr_dict.setdefault(fn_name, [])
    ctr_list.append(mosaic.put(ctr))


def add_fn_module_constructor(fn, ctr, name=None):
    module = inspect.getmodule(fn)
    _add_constructor(module, fn.__name__, ctr)


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
        module = inspect.getmodule(fn)
        name = fn.__name__
        attr_name = name
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
                attr_name = f'{name}_{idx}'
                setattr(module, attr_name, prev_fn)
                _copy_constructors(module, name, attr_name)
                idx += 1
            attr_name = f'{name}_{idx}'
            setattr(module, attr_name, fn)
        ctr = htypes.attr_constructors.parameter(
            path=[*self._path, fn.__name__],
            )
        _add_constructor(module, attr_name, ctr)
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
