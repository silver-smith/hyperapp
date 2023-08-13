from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    association_reg,
    mosaic,
    python_object_creg,
    web,
    types,
    )
from .code.mark import add_fn_module_constructor


def register(piece):
    code_registry_svc_res = web.summon(piece.service)
    t = python_object_creg.invite(piece.type)
    return Association(
        bases=[code_registry_svc_res, t],
        key_to_value={(code_registry_svc_res, t): piece.function},
        )


class DynCodeRegistry(CodeRegistry):

    def __init__(self, produce_name):
        super().__init__(produce_name, web, types)
        self.init_registries(association_reg, python_object_creg)

    def actor(self, t):
        def register(fn):
            type_res = python_object_creg.reverse_resolve(t)
            ctr = htypes.code_registry.constructor(
                service=mosaic.put(self._my_resource),
                type=mosaic.put(type_res),
                )
            add_fn_module_constructor(fn, ctr)
            return fn

        return register
