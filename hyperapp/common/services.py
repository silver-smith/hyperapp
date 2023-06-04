import logging
import sys
import threading
from collections import namedtuple
from functools import partial
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
from .cached_code_registry import CachedCodeRegistry
from .association_registry import AssociationRegistry
from .python_importer import PythonImporter
from .module_registry import CodeModule, ModuleRegistry
from .resource_dir import ResourceDir
from .unbundler import Unbundler
from ..resource.resource_type import ResourceType
from ..resource.resource_type_producer import resource_type_producer
from .meta_registry_association import register_meta_association
from ..resource.python_module import PythonModuleResourceType, python_module_pyobj
from .htypes.python_module import python_module_t
from .meta_association_type import MetaAssociationResourceType
from .pyobj_association_type import PyObjAssociationResourceType
from ..resource.pyobj_meta import register_pyobj_meta
from .htypes.meta_association import meta_association
from .htypes.pyobj_association import python_object_association_t
from ..resource.resource_registry import ResourceRegistry
from ..resource.resource_module import ResourceModule, load_resource_modules, load_resource_modules_list

log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'
HYPERAPP_DIR = Path(__file__).parent.parent.resolve()


class Services(object):

    builtin_services = [
        'services',
        'association_reg',
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
        'meta_registry',
        'module_registry',
        'on_stop',
        'stop_signal',
        'aux_unbundler_hooks',
        'unbundler',
        'resource_type_factory',
        'resource_type_reg',
        'python_object_creg',
        'resource_type_producer',
        'resource_registry_factory',
        'resource_registry',
        'resource_module_factory',
        'resource_loader',
        'resource_list_loader',
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
        self.meta_registry = CodeRegistry('meta', self.web, self.types)
        self.association_reg = AssociationRegistry(self.meta_registry)
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
        self.aux_unbundler_hooks = []
        self.unbundler = Unbundler(self.mosaic, self.association_reg, self.aux_unbundler_hooks)
        self.resource_type_factory = partial(ResourceType, self.types, self.mosaic, self.web)
        self.resource_type_reg = {}  # resource_t -> ResourceType instance
        self.python_object_creg = CachedCodeRegistry('python_object', self.web, self.types)
        register_meta_association(self.meta_registry, self.python_object_creg)
        self.resource_type_producer = partial(resource_type_producer, self.resource_type_factory, self.resource_type_reg)
        self.resource_type_reg[meta_association] = MetaAssociationResourceType()
        self.meta_registry.register_actor(
            python_object_association_t, partial(register_pyobj_meta, self.python_object_creg))
        self.resource_type_reg[python_object_association_t] = PyObjAssociationResourceType()
        self.resource_type_reg[python_module_t] = PythonModuleResourceType()
        self.python_object_creg.register_actor(
            python_module_t, python_module_pyobj, self.mosaic, self.python_importer, self.python_object_creg)
        self.resource_registry_factory = partial(ResourceRegistry, self.mosaic)
        self.resource_registry = self.resource_registry_factory()
        self.resource_module_factory = partial(
            ResourceModule,
            self.mosaic,
            self.resource_type_producer,
            self.python_object_creg,
        )
        self.resource_loader = partial(
            load_resource_modules,
            self.resource_module_factory,
            )
        self.resource_list_loader = partial(
            load_resource_modules_list,
            self.resource_module_factory,
            )

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
