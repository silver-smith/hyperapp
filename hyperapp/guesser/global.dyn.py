import logging

from . import htypes
from .services import (
    mosaic,
    python_object_creg,
    runner_method_get_resource_type_ref,
    )

_log = logging.getLogger(__name__)


class GlobalVisitor:

    def __init__(self, fixtures_module, on_global):
        self._fix_module = fixtures_module
        self._on_global = on_global

    def run(self, process, module, globl):
        get_resource_type = process.rpc_call(runner_method_get_resource_type_ref)

        attr = htypes.attribute.attribute(
            object=mosaic.put(module),
            attr_name=globl.name,
            )
        attr_ref = mosaic.put(attr)

        if isinstance(globl, htypes.inspect.fn_attr):
            kw = {
                name: self._fixture(globl.name, name)
                for name in globl.param_list
                }
            if kw:
                fn = htypes.partial.partial(
                    function=attr_ref,
                    params=[
                        htypes.partial.param(name, value)
                        for name, value in kw.items()
                        ],
                    )
                fn_ref = mosaic.put(fn)
            else:
                fn_ref = attr_ref

            call = htypes.call.call(fn_ref)
            value_ref = mosaic.put(call)
        else:
            value_ref = attr_ref

        result_t = get_resource_type(value_ref)
        _log.info("%r type: %r", globl.name, result_t)

        self._on_global(process, globl, result_t)

    def _fixture(self, globl_name, param__name):
        res_name = f'param.{globl_name}.{param_name}'
        try:
            fixture_res = self._fix_module[res_name]
        except KeyError:
            raise RuntimeError("Fixture {res_name!r} is not defined at: {self._fix_module.name}")
        return python_object_creg.animate(fixture_res)
