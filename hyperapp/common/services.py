import logging
import sys
import threading
from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace

from .htypes import BuiltinTypeRegistry, register_builtin_types
from .code_module import code_module_t
from .ref import ref_repr
from .mosaic import Mosaic
from .web import Web
from .module_ref_resolver import ModuleRefResolver
from .type_module_loader import TypeModuleLoader
from .type_system import TypeSystem
from .code_module import register_code_module_types
from .code_module_loader import CodeModuleRegistry, CodeModuleLoader
from .code_registry import CodeRegistry
from .python_importer import PythonImporter
from .module_registry import CodeModule, ModuleRegistry
from .resource_dir import ResourceDir

log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'
HYPERAPP_DIR = Path(__file__).parent.parent.resolve()


class Services(object):

    builtin_services = [
        'services',
        'builtin_services',
        'builtin_types',
        'hyperapp_dir',
        'module_dir_list',
        'mosaic',
        'types',
        'web',
        'local_types',
        'local_modules',
        'type_module_loader',
        'code_module_loader',
        'module_registry',
    ]

    def __init__(self, module_dir_list, additional_resource_dirs=None):
        self.hyperapp_dir = HYPERAPP_DIR
        self.resource_dir_list = [
            ResourceDir(HYPERAPP_DIR, module_dir_list),
            *(additional_resource_dirs or []),
            ]
        self.module_dir_list = module_dir_list
        self.on_start = []
        self.on_stop = []
        self.stop_signal = threading.Event()
        self._is_stopped = False

    def init_services(self):
        log.info("Init services.")
        self.services = self  # Allows resources to access services itself.
        self.builtin_types = BuiltinTypeRegistry()
        self.types = TypeSystem()
        self.web = Web(self.types)
        self.mosaic = Mosaic(self.types)
        self.types.init(self.builtin_types, self.mosaic)
        self.module_ref_resolver = ModuleRefResolver(self.mosaic)
        self.web.add_source(self.mosaic)
        register_builtin_types(self.builtin_types, self.mosaic, self.types)
        register_code_module_types(self.builtin_types, self.mosaic, self.types)
        self.local_types = {}  # module name -> name -> name_wrapped_mt ref.
        # CodeModuleRegistry: by_name: name -> code_module_t, by_requirement: name -> code_module_t set.
        self.local_modules = CodeModuleRegistry()
        self.type_module_loader = TypeModuleLoader(self.builtin_types, self.mosaic, self.types)
        self.code_module_loader = CodeModuleLoader(self.hyperapp_dir, self.mosaic)
        self.python_importer = PythonImporter()
        self._module_code_registry = CodeRegistry('module', self.web, self.types)
        self._module_code_registry.register_actor(code_module_t, CodeModule.from_piece, self.types, self.web)
        self.module_registry = ModuleRegistry(self.mosaic, self.web, self.python_importer, self._module_code_registry, self.on_start)
        self.python_importer.register_meta_hook()

    def stop(self):
        log.info("Stop services.")
        assert not self._is_stopped
        log.info('Stopping modules...')
        for stop in reversed(self.on_stop):
            stop()
        log.info('Stopping modules: done')
        self.python_importer.remove_modules()
        self._is_stopped = True
        log.info("Services are stopped.")

    def init_modules(self, code_module_list, config=None):
        log.info("Init modules.")
        try:
            self.type_module_loader.load_type_modules(self.module_dir_list, self.local_types)
            self._load_code_module_list(code_module_list, config or {})
        except:
            self.python_importer.unregister_meta_hook()
            raise

    def start_modules(self):
        for start in self.on_start:
            log.info("Call module start: %s", start)
            start()

    def unregister_import_meta_hook(self):
        self.python_importer.unregister_meta_hook()

    def _load_code_module_list(self, module_name_list, config):
        self.code_module_loader.load_code_modules(self.local_types, self.module_dir_list, self.local_modules)
        module_list = [
            self.local_modules.by_name[name]
            for name in module_name_list
            ]
        self.module_registry.import_module_list(self, module_list, self.local_modules.by_requirement, config, start_modules=False)
