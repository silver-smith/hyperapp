import logging
import sys
import threading
from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace

from .htypes import BuiltinTypeRegistry, register_builtin_types
from .ref import ref_repr
from .mosaic import Mosaic
from .web import Web
from .module_ref_resolver import ModuleRefResolver
from .type_module_loader import TypeModuleLoader
from .type_system import TypeSystem
from .code_module import register_code_module_types
from .code_module_loader import CodeModuleLoader
from .code_module_importer import CodeModuleImporter
from .module import ModuleRegistry

log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()

ModuleRec = namedtuple('ModuleRec', 'module module_ref')


class Services(object):

    def __init__(self):
        self.hyperapp_dir = HYPERAPP_DIR / 'hyperapp'
        self.code_module_dir_list = [self.hyperapp_dir]
        self.on_start = []
        self.on_stop = []
        self.stop_signal = threading.Event()
        self._is_stopped = False

    def init_services(self):
        log.info("Init services.")
        self.builtin_types = BuiltinTypeRegistry()
        self.types = TypeSystem()
        self.web = Web(self.types)
        self.mosaic = Mosaic(self.types)
        self.types.init(self.builtin_types, self.mosaic)
        self.module_ref_resolver = ModuleRefResolver(self.mosaic)
        self.web.add_source(self.mosaic)
        register_builtin_types(self.builtin_types, self.mosaic, self.types)
        register_code_module_types(self.builtin_types, self.mosaic, self.types)
        self.type_module_loader = TypeModuleLoader(self.builtin_types, self.mosaic, self.types)
        self.code_module_loader = CodeModuleLoader(self.mosaic, self.type_module_loader.registry)
        self.module_registry = ModuleRegistry()
        self.code_module_importer = CodeModuleImporter(self.mosaic, self.types)
        self.code_module_importer.register_meta_hook()
        self.imported_code_modules = {}  # full code module name -> ModuleRec

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

    def init_modules(self, code_module_list, config=None):
        log.info("Init modules.")
        try:
            self.type_module_loader.load_type_modules(self.hyperapp_dir)
            self._load_code_module_list(code_module_list, config)
            self.module_registry.init_phases(self)
        finally:
            self.code_module_importer.unregister_meta_hook()

    def _load_code_module_list(self, module_name_list, config):

        registry = self.code_module_loader.load_code_modules(self.code_module_dir_list)
        self.available_code_modules = registry.by_name

        preferred_modules = {
            registry.by_name[module_name]
            for module_name in module_name_list
            }
        for module_name in module_name_list:
            log.info("Require import module %r", module_name)
            self.code_module_importer.import_code_module(
                registry.by_requirement, registry.by_name[module_name], preferred_modules)
        module_name_by_ref = {
            module_ref: module_name
            for module_name, module_ref in registry.by_name.items()
            }
        # Should init modules in the same order as they were imported.
        for module_ref, module in self.code_module_importer.registry.items():
            module_name = module_name_by_ref[module_ref]
            if config:
                module_config = config.get(module_name, {})
            else:
                module_config = {}
            self._init_module(module_name, module, module_config)
            self.imported_code_modules[module_name] = ModuleRec(module, module_ref)

    def _init_module(self, module_name, module, config):
        this_module_class = module.__dict__.get('ThisModule')
        if this_module_class:
            log.info("Init module %s (%s) with config: %s", module_name, this_module_class, config)
            this_module = this_module_class(module_name, self, config)
            module.__dict__['this_module'] = this_module
            self.module_registry.register(this_module)
