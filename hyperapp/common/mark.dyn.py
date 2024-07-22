import inspect
from functools import partial
from types import SimpleNamespace

from hyperapp.common.htypes import Type
from hyperapp.common.resource_ctr import (
    add_fn_module_constructor,
    )

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )


class ServiceMarker:

    def __call__(self, fn):
        ctr = htypes.rc_constructors.service(
            attr_name=fn.__name__,
            name=fn.__name__,
            )
        add_fn_module_constructor(fn, mosaic.put(ctr))
        return fn


def service2_marker(fn):
    ctr = htypes.rc_constructors.service2(
        attr_name=fn.__name__,
        name=fn.__name__,
        )
    add_fn_module_constructor(fn, mosaic.put(ctr))
    return fn


def fixture_marker(fn):
    ctr = htypes.rc_constructors.fixture(
        attr_name=fn.__name__,
        name=fn.__name__,
        )
    add_fn_module_constructor(fn, mosaic.put(ctr))
    return fn


def model(fn):
    ctr = htypes.rc_constructors.model(
        attr_name=fn.__name__,
        )
    add_fn_module_constructor(fn, mosaic.put(ctr))
    return fn


class UiCommandBase:

    def __call__(self, fn_or_t):
        if isinstance(fn_or_t, Type):  # Parameterized version.
            t_ref = pyobj_creg.actor_to_ref(fn_or_t)
            return partial(self._ui_command_wrapper, t_ref)
        else:  # Non-parameterized version.
            name = fn_or_t.__name__
            params = tuple(inspect.signature(fn_or_t).parameters)
            ctr = self.universal_command_ctr(name, name, params)
            add_fn_module_constructor(fn_or_t, mosaic.put(ctr))
            return fn_or_t

    def _ui_command_wrapper(self, t_ref, fn):
        name = fn.__name__
        params = tuple(inspect.signature(fn).parameters)
        ctr = self.command_ctr(name, t_ref, name, params)
        add_fn_module_constructor(fn, mosaic.put(ctr))
        return fn


class UiCommand(UiCommandBase):
    universal_command_ctr = htypes.rc_constructors.universal_ui_command    
    command_ctr = htypes.rc_constructors.ui_command


class UiModelCommand(UiCommandBase):
    universal_command_ctr = htypes.rc_constructors.universal_ui_model_command    
    command_ctr = htypes.rc_constructors.ui_model_command


def mark():
    return SimpleNamespace(
        service=ServiceMarker(),
        service2=service2_marker,
        fixture=fixture_marker,
        model=model,
        ui_command=UiCommand(),
        ui_model_command=UiModelCommand(),
        )
