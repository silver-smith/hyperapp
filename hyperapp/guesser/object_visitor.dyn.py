import logging

from .services import (
    mosaic,
    runner_method_collect_attributes_ref,
    web,
    )

_log = logging.getLogger(__name__)


class ObjectVisitor:

    def __init__(self, on_attr):
        self._on_attr = on_attr

    def run(self, process, object_res, path, constructor_ctx):
        collect_attributes = process.rpc_call(runner_method_collect_attributes_ref)

        attr_ref_list = collect_attributes(mosaic.put(object_res))
        attr_list = [web.summon(ref) for ref in attr_ref_list]
        _log.info("Collected attr list: %s", attr_list)

        for attr in attr_list:
            self._on_attr(process, object_res, path, attr, constructor_ctx)
