import inspect
from functools import partial
from types import SimpleNamespace

from hyperapp.common.htypes import Type
from hyperapp.common.resource_ctr import (
    RESOURCE_ATTR_CTR_NAME,
    add_attr_constructor,
    add_fn_attr_constructor,
    )

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )


def _copy_constructors(module, source_name, target_name):
    ctr_dict = module.__dict__.setdefault(RESOURCE_ATTR_CTR_NAME, {})
    source_ctr_list = ctr_dict.setdefault(source_name, [])
    target_ctr_list = ctr_dict.setdefault(target_name, [])
    target_ctr_list += source_ctr_list


class ServiceMarker:

    def __call__(self, fn):
        ctr = htypes.rc_constructors.service(
            name=fn.__name__,
            )
        add_fn_attr_constructor(fn, mosaic.put(ctr))
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
        ctr = htypes.rc_constructors.parameter(
            path=(*self._path, fn.__name__),
            )
        add_attr_constructor(module, attr_name, mosaic.put(ctr))
        return fn


def model(fn):
    ctr = htypes.rc_constructors.model_ctr()
    add_fn_attr_constructor(fn, mosaic.put(ctr))
    return fn


class UiCommandBase:

    def __call__(self, fn_or_t):
        if isinstance(fn_or_t, Type):  # Parameterized version.
            t_res = pyobj_creg.reverse_resolve(fn_or_t)
            t_ref = mosaic.put(t_res)
            return partial(self._ui_command_wrapper, t_ref)
        else:  # Non-parameterized version.
            name = fn_or_t.__name__
            params = tuple(inspect.signature(fn_or_t).parameters)
            ctr = self.universal_command_ctr(name, params)
            add_fn_attr_constructor(fn_or_t, mosaic.put(ctr))
            return fn_or_t

    def _ui_command_wrapper(self, t_ref, fn):
        name = fn.__name__
        params = tuple(inspect.signature(fn).parameters)
        ctr = self.command_ctr(t_ref, name, params)
        add_fn_attr_constructor(fn, mosaic.put(ctr))
        return fn


class UiCommand(UiCommandBase):
    universal_command_ctr = htypes.rc_constructors.universal_ui_command_ctr    
    command_ctr = htypes.rc_constructors.ui_command_ctr


class UiModelCommand(UiCommandBase):
    universal_command_ctr = htypes.rc_constructors.universal_ui_model_command_ctr    
    command_ctr = htypes.rc_constructors.ui_model_command_ctr


def mark():
    return SimpleNamespace(
        param=ParamMarker(),
        service=ServiceMarker(),
        model=model,
        ui_command=UiCommand(),
        ui_model_command=UiModelCommand(),
        )
