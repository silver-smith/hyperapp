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

        object_attrs = collect_attributes(object_ref=mosaic.put(object_res))
        attr_list = [web.summon(ref) for ref in object_attrs.attr_list]
        _log.info("Collected attr list, module %s: %s", object_attrs.object_module, attr_list)

        if module_name:
            if object_attrs.object_module != module_name:
                return  # Skip types from other modules.
        else:
            module_name = object_attrs.object_module

        for attr in attr_list:
            self._on_attr(process, object_res, module_name, path, attr, constructor_ctx)
