import logging

from . import htypes
from .services import (
    auto_importer_imports_ref,
    auto_importer_loader_ref,
    mosaic,
    runner_method_collect_attributes_ref,
    web,
    )

_log = logging.getLogger(__name__)


class ModuleVisitor:

    def __init__(self, on_module, on_global):
        self._on_module = on_module
        self._on_global = on_global

    def run(self, process, module_name, source_path):
        collect_attributes = process.rpc_call(runner_method_collect_attributes_ref)
        auto_importer_imports = process.rpc_call(auto_importer_imports_ref)

        loader = auto_importer_loader_ref
        module = htypes.python_module.python_module(
            module_name=module_name,
            source=source_path.read_text(),
            file_path=str(source_path),
            import_list=[
                htypes.python_module.import_rec('*', loader),
                ],
            )

        global_ref_list = collect_attributes(mosaic.put(module))
        global_list = [web.summon(ref) for ref in global_ref_list]
        _log.info("Collected global list: %s", global_list)

        for attr in global_list:
            self._on_global(process, module, attr)

        imports = auto_importer_imports()
        _log.info("Import list: %s", imports)

        self._on_module(module_name, source_path, imports)
