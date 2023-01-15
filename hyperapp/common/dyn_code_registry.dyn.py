from hyperapp.common.code_registry import CodeRegistry

from . import htypes
from .services import (
    mosaic,
    python_object_creg,
    )
from .code.mark import add_fn_module_constructor


def register(piece):
    code_registry_svc = python_object_creg.invite(piece.service)
    t = python_object_creg.invite(piece.type)
    fn = python_object_creg.invite(piece.function)
    code_registry_svc.register_actor(t, fn)


class DynCodeRegistry(CodeRegistry):

    def actor(self, t):
        def register(fn):
            service_res = python_object_creg.reverse_resolve(self)
            type_res = python_object_creg.reverse_resolve(t)
            ctr = htypes.code_registry.constructor(
                service=mosaic.put(service_res),
                type=mosaic.put(type_res),
                )
            add_fn_module_constructor(fn, ctr)
            return fn

        return register
