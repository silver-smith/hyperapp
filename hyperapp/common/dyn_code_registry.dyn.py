from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    association_reg,
    mosaic,
    pyobj_creg,
    web,
    types,
    )
from .code.mark import add_fn_module_constructor


class DynCodeRegistry(CodeRegistry):

    def __init__(self, produce_name):
        super().__init__(produce_name, web, types)
        self.init_registries(association_reg, pyobj_creg)

    def actor(self, t):
        def register(fn):
            type_res = pyobj_creg.reverse_resolve(t)
            ctr = htypes.code_registry.constructor(
                service=mosaic.put(self._my_resource),
                type=mosaic.put(type_res),
                )
            add_fn_module_constructor(fn, ctr)
            return fn

        return register
