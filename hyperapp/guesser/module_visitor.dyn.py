import logging

from . import htypes
from .services import (
    auto_importer_imports_ref,
    auto_importer_ref,
    )

_log = logging.getLogger(__name__)


class ModuleVisitor:

    def __init__(self, on_object, on_module):
        self._on_object = on_object
        self._on_module = on_module

    def run(self, process, module_name, source_path):
        auto_importer_imports = process.rpc_call(auto_importer_imports_ref)

        loader = auto_importer_ref
        module_res = htypes.python_module.python_module(
            module_name=module_name,
            source=source_path.read_text(),
            file_path=str(source_path),
            import_list=[
                htypes.python_module.import_rec('*', loader),
                ],
            )

        self._on_object(process, module_res, path=[])

        imports = auto_importer_imports()
        _log.info("Import list: %s", imports)

        self._on_module(module_name, source_path, imports)
