import logging

from . import htypes
from .services import (
    mosaic,
    python_object_creg,
    runner_method_get_resource_type_ref,
    )

_log = logging.getLogger(__name__)


class AttrVisitor:

    def __init__(self, fixtures_module, on_attr):
        self._fix_module = fixtures_module
        self._on_attr = on_attr

    def run(self, process, object_res, attr):
        _log.info("Loading type for global: %r", attr.name)
        get_resource_type = process.rpc_call(runner_method_get_resource_type_ref)

        attr_res = htypes.attribute.attribute(
            object=mosaic.put(object_res),
            attr_name=attr.name,
            )
        attr_ref = mosaic.put(attr_res)

        if isinstance(attr, htypes.inspect.fn_attr):
            kw = {
                name: self._fixture(attr.name, name)
                for name in attr.param_list
                }
            if kw:
                fn = htypes.partial.partial(
                    function=attr_ref,
                    params=[
                        htypes.partial.param(
                            name=name,
                            value=mosaic.put(value),
                            )
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
        _log.info("%r type: %r", attr.name, result_t)

        self._on_attr(process, attr, result_t)

    def _fixture(self, attr_name, param_name):
        res_name = f'param.{attr_name}.{param_name}'
        if not self._fix_module:
            raise RuntimeError(f"Fixture {res_name!r} is required but fixtures module does not exist")
        try:
            return self._fix_module[res_name]
        except KeyError:
            raise RuntimeError(f"Fixture {res_name!r} is not defined at: {self._fix_module.name}")
