import logging

from . import htypes
from .services import (
    mosaic,
    )

_log = logging.getLogger(__name__)


class ModuleVisitor:

    def __init__(self, import_resources, on_object, on_module):
        self._import_resources = import_resources
        self._on_object = on_object
        self._on_module = on_module

    def run(self, process, module_name, source_path):

        resources = [
            htypes.auto_importer.resource(import_name, rec.resource_ref)
            for import_name, rec in self._import_resources.items()
            ]
        auto_importer_res = htypes.auto_importer.auto_importer(resources)
        module_res = htypes.python_module.python_module(
            module_name=module_name,
            source=source_path.read_text(),
            file_path=str(source_path),
            import_list=[
                htypes.python_module.import_rec('*', mosaic.put(auto_importer_res)),
                ],
            )

        self._on_object(process, module_res, path=[], constructor_ctx=None)

        auto_importer = process.proxy(mosaic.put(auto_importer_res))
        imports = auto_importer.imports()
        _log.info("Import list: %s", imports)

        self._on_module(module_name, source_path, imports)
