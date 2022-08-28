import logging

from . import htypes
from .services import (
    mosaic,
    collect_attributes_ref,
    web,
    )

_log = logging.getLogger(__name__)


class ObjectVisitor:

    def __init__(self, on_attr):
        self._on_attr = on_attr

    def run(self, process, object_res, module_name, path, constructor_ctx):
        _log.info("Visiting object %s: %r", path, object_res)
        collect_attributes = process.rpc_call(collect_attributes_ref)

        attr_ref_list = collect_attributes(mosaic.put(object_res))
        attr_list = [web.summon(ref) for ref in attr_ref_list]
        _log.info("Collected attr list: %s", attr_list)

        for attr in attr_list:
            if isinstance(attr, htypes.inspect.fn_attr):
                if not module_name:
                    module_name = attr.module
                elif attr.module != module_name:
                    continue  # Skip types from other modules.
            self._on_attr(process, object_res, module_name, path, attr, constructor_ctx)
