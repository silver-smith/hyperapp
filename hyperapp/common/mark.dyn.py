import inspect
from types import SimpleNamespace

from hyperapp.common.htypes import Type
from hyperapp.common.resource_ctr import (
    RESOURCE_CTR_ATTR,
    add_constructor,
    add_fn_module_constructor,
    )

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )


def _copy_constructors(module, source_name, target_name):
    ctr_dict = module.__dict__.setdefault(RESOURCE_CTR_ATTR, {})
    source_ctr_list = ctr_dict.setdefault(source_name, [])
    target_ctr_list = ctr_dict.setdefault(target_name, [])
    target_ctr_list += source_ctr_list


class ServiceMarker:

    def __call__(self, fn):
        ctr = htypes.attr_constructors.service(
            name=fn.__name__,
            )
        add_fn_module_constructor(fn, mosaic.put(ctr))
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
            path=(*self._path, fn.__name__),
            )
        add_constructor(module, attr_name, mosaic.put(ctr))
        return fn


def global_command(fn):
    ctr = htypes.global_command_ctr.global_command_ctr()
    add_fn_module_constructor(fn, mosaic.put(ctr))
    return fn


def object_command(fn):
    ctr = htypes.object_command_ctr.object_command_ctr()
    add_fn_module_constructor(fn, mosaic.put(ctr))
    return fn


def ui_command(fn_or_t):
    if isinstance(fn_or_t, Type):  # Parameterized version.
        t_res = pyobj_creg.reverse_resolve(fn_or_t)
        t_ref = mosaic.put(t_res)
        ctr = htypes.attr_constructors.ui_command_ctr(t_ref)

        def _ui_command(fn):
            add_fn_module_constructor(fn, mosaic.put(ctr))
            return fn

        return _ui_command
    else:  # Non-parameterized version.
        ctr = htypes.attr_constructors.universal_ui_command_ctr()
        add_fn_module_constructor(fn_or_t, mosaic.put(ctr))
        return fn_or_t


def mark():
    return SimpleNamespace(
        param=ParamMarker(),
        service=ServiceMarker(),
        global_command=global_command,
        object_command=object_command,
        ui_command=ui_command,
        )
