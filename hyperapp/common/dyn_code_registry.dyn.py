from functools import cached_property

from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    association_reg,
    mosaic,
    python_object_creg,
    web,
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

    @cached_property
    def _my_resource(self):
        return python_object_creg.reverse_resolve(self)

    def _resolve_record(self, t):
        try:
            return super()._resolve_record(t)
        except KeyError:
            fn_res = association_reg[self._my_resource, t]
            try:
                fn = python_object_creg.invite(fn_res)
                return self._Rec(fn, args=[], kw={})
            except KeyError as x:
                # Do not let KeyError out - it will be caught by superclass and incorrect error message will be produced.
                raise RuntimeError(f"{self._produce_name}: Error resolving function for {t!r}, {fn_res}: {x}")
