import logging
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

from .htypes import BuiltinTypeRegistry, register_builtin_types, register_service_types
from .ref import ref_repr
from .local_type_module import LocalTypeModuleRegistry
from .code_module import code_module_t
from .mosaic import Mosaic
from .web import Web
from .module_ref_resolver import ModuleRefResolver
from .type_module_loader import TypeModuleLoader
from .type_system import TypeSystem
from .code_module import LocalCodeModuleRegistry, register_code_module_types
from .code_module_loader import CodeModuleLoader
from .code_module_importer import CodeModuleImporter
from .module import ModuleRegistry

log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()


class Services(object):

    def __init__(self):
        self.hyperapp_dir = HYPERAPP_DIR / 'hyperapp'
        self.interface_dir = self.hyperapp_dir / 'common' / 'interface'
        self.on_start = []
        self.on_stop = []
        self.stop_signal = threading.Event()
        self._is_stopped = False
        self.name2module = {}  # module name (x.y.z) -> imported module

    def init_services(self):
        log.info("Init services.")
        self.web = Web()
        self.builtin_types = BuiltinTypeRegistry()
        self.types = TypeSystem()
        self.mosaic = Mosaic(self.types)
        self.types.init(self.builtin_types, self.mosaic)
        self.module_ref_resolver = ModuleRefResolver(self.mosaic)
        self.web.add_source(self.mosaic)
        register_builtin_types(self.builtin_types, self.mosaic, self.types)
        register_service_types(self.builtin_types, self.mosaic, self.types)
        register_code_module_types(self.builtin_types, self.mosaic, self.types)
        self.local_type_module_registry = LocalTypeModuleRegistry()
        self.local_code_module_registry = LocalCodeModuleRegistry()
        self.type_module_loader = TypeModuleLoader(self.builtin_types, self.mosaic, self.types, self.local_type_module_registry)
        self.code_module_loader = CodeModuleLoader(self.mosaic, self.local_type_module_registry, self.local_code_module_registry)
        self.module_registry = ModuleRegistry()
        self.code_module_importer = CodeModuleImporter(self.mosaic, self.types)
        self.code_module_importer.register_meta_hook()

    def start(self):
        log.info("Start services.")
        for start in self.on_start:
            start()

    def stop(self):
        log.info("Stop services.")
        assert not self._is_stopped
        log.info('Stopping modules...')
        for stop in reversed(self.on_stop):
            stop()
        log.info('Stopping modules: done')
        self._is_stopped = True
        log.info("Services are stopped.")

    def init_modules(self, type_module_list, code_module_list, config=None):
        log.info("Init modules.")
        try:
            self._load_type_module_list(type_module_list)
            self._load_code_module_list(code_module_list, config)
            self.module_registry.init_phases(self)
        finally:
            self.code_module_importer.unregister_meta_hook()
        
    def _load_type_module_list(self, module_name_list):
        for module_name in module_name_list:
            file_path = self.interface_dir.joinpath(module_name).with_suffix(TYPE_MODULE_EXT)
            self.type_module_loader.load_type_module(file_path, module_name)

    def _load_code_module_list(self, module_name_list, config):
        for module_name in module_name_list:
            if config:
                module_config = config.get(module_name, {})
            else:
                module_config = {}
            parts = module_name.split('.')
            file_path = self.hyperapp_dir.joinpath(*parts)
            code_module = self.code_module_loader.load_code_module(file_path, module_name)
            code_module_ref = self.mosaic.put(code_module)
            log.info("Import module %s (%s) with file path %s", module_name, ref_repr(code_module_ref), file_path)
            module = self.code_module_importer.import_code_module(code_module_ref)
            self.name2module[module_name] = module
            self._init_module(code_module.module_name, module, module_config)

    def _init_module(self, module_name, module, config):
        this_module_class = module.__dict__.get('ThisModule')
        if this_module_class:
            log.info("Init module %s (%s) with config: %s", module_name, this_module_class, config)
            this_module = this_module_class(module_name, self, config)
            module.__dict__['this_module'] = this_module
            self.module_registry.register(this_module)
