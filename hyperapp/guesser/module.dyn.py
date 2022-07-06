import logging

from . import htypes
from .services import (
    auto_importer_loader_ref,
    mosaic,
    runner_method_collect_attributes_ref,
    )

_log = logging.getLogger(__name__)


class ModuleVisitor:

    def __init__(self):
        pass

    def run(self, process, module_name, source_path):
        collect_attributes = process.rpc_call(runner_method_collect_attributes_ref)

        loader = auto_importer_loader_ref
        module = htypes.python_module.python_module(
            module_name=module_name,
            source=source_path.read_text(),
            file_path=str(source_path),
            import_list=[
                htypes.python_module.import_rec('*', loader),
                ],
            )

        global_list = collect_attributes(mosaic.put(module))
        _log.info("Collected global list: %s", global_list)
