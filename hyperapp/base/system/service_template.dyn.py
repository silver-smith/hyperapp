import inspect
from functools import partial

from . import htypes
from .services import (
    pyobj_creg,
    )


def resolve_service_cfg_item(piece):
    return (piece.name, piece)


def _resolve_service_args(system, piece):
    if piece.want_config:
        config_args = [system.resolve_config(piece.name)]
    else:
        config_args = []
    service_args = [
        system.resolve_service(name)
        for name in piece.service_params
        ]
    return [*config_args, *service_args]


def resolve_service_cfg_value(piece, key, system, service_name):
    fn = pyobj_creg.invite(piece.function)
    service_args = _resolve_service_args(system, piece)
    if piece.free_params:
        return partial(fn, *service_args)
    else:
        return fn(*service_args)


def _finalize(fn, gen):
    try:
        next(gen)
    except StopIteration:
        pass
    else:
        raise RuntimeError(f"Generator function {fn!r} should have only one 'yield' statement")


def resolve_finalizer_gen_service_cfg_value(piece, key, system, service_name):
    fn = pyobj_creg.invite(piece.function)
    if not inspect.isgeneratorfunction(fn):
        raise RuntimeError(f"Function {fn!r} expected to be a generator function")
    service_args = _resolve_service_args(system, piece)
    gen = fn(*service_args)
    service = next(gen)
    system.add_finalizer(piece.name, partial(_finalize, fn, gen))
    return service


def service_template_cfg_item_config():
    return {
        htypes.system.service_template: resolve_service_cfg_item,
        htypes.system.finalizer_gen_service_template: resolve_service_cfg_item,
        }


def service_template_cfg_value_config():
    return {
        htypes.system.service_template: resolve_service_cfg_value,
        htypes.system.finalizer_gen_service_template: resolve_finalizer_gen_service_cfg_value,
        }
