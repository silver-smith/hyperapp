from pathlib import Path
import sys
from types import SimpleNamespace
import logging

from .htypes import register_builtin_types
from .logger import log, init_logger, close_logger
from .logger_json_storage import json_file_log_storage_session
from .local_type_module import LocalTypeModuleRegistry
from .code_module import code_module_t
from .ref_registry import RefRegistry
from .ref_resolver import RefResolver
from .module_ref_resolver import ModuleRefResolver
from .type_module_loader import TypeModuleLoader
from .type_system import TypeSystem
from .code_module import LocalCodeModuleRegistry, register_code_module_types
from .code_module_loader import CodeModuleLoader
from .code_module_importer import CodeModuleImporter
from .module import ModuleRegistry

_log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()


class Services(object):

    def __init__(self):
        self.hyperapp_dir = HYPERAPP_DIR / 'hyperapp'
        self.interface_dir = self.hyperapp_dir / 'common' / 'interface'
        self.on_start = []
        self.on_stop = []
        self.config = {}
        self._is_stopped = False
        self.name2module = {}  # module name (x.y.z) -> imported module

    def init_services(self, config=None):
        self.config.update(config or {})
        self.ref_resolver = RefResolver()
        self.types = TypeSystem(self.ref_resolver)
        self.ref_registry = RefRegistry(self.types)
        self.module_ref_resolver = ModuleRefResolver(self.ref_registry)
        self.ref_resolver.add_source(self.ref_registry)
        register_builtin_types(self.ref_registry, self.types)
        register_code_module_types(self.ref_registry, self.types)
        self._logger_storage = json_file_log_storage_session(self.ref_resolver, self.types)
        self.logger = init_logger(self.types, self.ref_registry, self.module_ref_resolver, self._logger_storage)
        log.session_started()
        self.local_type_module_registry = LocalTypeModuleRegistry()
        self.local_code_module_registry = LocalCodeModuleRegistry()
        self.type_module_loader = TypeModuleLoader(self.types, self.ref_registry, self.local_type_module_registry)
        self.code_module_loader = CodeModuleLoader(self.ref_registry, self.local_type_module_registry, self.local_code_module_registry)
        self.module_registry = ModuleRegistry()
        self.code_module_importer = CodeModuleImporter(self.types)
        self.code_module_importer.register_meta_hook()

    def start(self):
        for start in self.on_start:
            start()

    def stop(self):
        if self._is_stopped:
            _log.info('Already stopped.')
            return
        _log.info('Stopping modules...')
        for stop in self.on_stop:
            stop()
        _log.info('Stopping modules: done')
        self.on_stopped()
        log.session_stopped()
        close_logger()
        self._logger_storage.close()
        self._is_stopped = True

    def on_stopped(self):
        pass

    def init_modules(self, type_module_list, code_module_list, config=None):
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
                module_config = config.get(module_name)
            else:
                module_config = None
            parts = module_name.split('.')
            file_path = self.hyperapp_dir.joinpath(*parts)
            code_module = self.code_module_loader.load_code_module(file_path, module_name)
            code_module_ref = self.ref_registry.distil(code_module)
            module = self.code_module_importer.import_code_module(code_module_ref)
            self.name2module[module_name] = module
            self._init_module(code_module.module_name, module, module_config)

    def _init_module(self, module_name, module, config):
        this_module_class = module.__dict__.get('ThisModule')
        if this_module_class:
            this_module = this_module_class(module_name, self, config)
            module.__dict__['this_module'] = this_module
            self.module_registry.register(this_module)
