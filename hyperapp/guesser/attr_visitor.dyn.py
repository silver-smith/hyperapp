import logging

from . import htypes
from .services import (
    mosaic,
    python_object_creg,
    get_resource_type_ref,
    )

_log = logging.getLogger(__name__)


class AttrVisitor:

    def __init__(self, fixtures_module, on_attr, on_object=None):
        self._fix_module = fixtures_module
        self._on_attr = on_attr
        self._on_object = on_object

    def run(self, process, object_res, module_name, path, attr, constructor_ctx):
        _log.info("Loading type for attribute %s: %r", path, attr.name)
        get_resource_type = process.rpc_call(get_resource_type_ref)

        attr_res = htypes.attribute.attribute(
            object=mosaic.put(object_res),
            attr_name=attr.name,
            )
        attr_ref = mosaic.put(attr_res)

        if isinstance(attr, htypes.inspect.fn_attr):
            kw = {
                name: self._fixture(path, attr.name, name)
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

            value_res = htypes.call.call(fn_ref)
            value_ref = mosaic.put(value_res)
        else:
            value_res = attr_res
            value_ref = attr_ref

        result_t = get_resource_type(resource_ref=value_ref)
        _log.info("%s/%s type: %r", constructor_ctx or '', attr.name, result_t)

        if isinstance(result_t, htypes.inspect.coroutine_fn_t):
            async_call = htypes.async_call.async_call(fn_ref)
            async_call_ref = mosaic.put(async_call)
            result_t = get_resource_type(resource_ref=async_call_ref)
            _log.info("%s/%s async call type: %r", constructor_ctx or '', attr.name, result_t)

        attr_ctx = self._on_attr(process, attr, result_t, constructor_ctx)

        if attr.module != module_name:
            return  # Skip types from other modules.
        if not self._on_object:
            return
        if not isinstance(result_t, htypes.inspect.object_t):
            return
        self._on_object(process, value_res, module_name, path=[*path, attr.name], constructor_ctx=attr_ctx)

    def _fixture(self, path, attr_name, param_name):
        res_name = '.'.join(['param', *path, attr_name, param_name])
        if not self._fix_module:
            raise RuntimeError(f"Fixture {res_name!r} is required but fixtures module does not exist")
        try:
            return self._fix_module[res_name]
        except KeyError:
            raise RuntimeError(f"Fixture {res_name!r} is not defined at: {self._fix_module.name}")
