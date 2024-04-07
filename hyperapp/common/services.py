import logging
import sys
import threading
from collections import namedtuple
from functools import partial
from pathlib import Path
from types import SimpleNamespace

from .htypes import BuiltinTypeRegistry, register_builtin_types
from .ref import ref_repr
from .mosaic import Mosaic
from .web import Web
from .type_module_loader import TypeModuleLoader
from .type_system import TypeSystem
from .code_registry import CodeRegistry
from .pyobj_registry import PyObjRegistry
from .association_registry import AssociationRegistry
from .python_importer import PythonImporter
from .resource_dir import ResourceDir
from .unbundler import Unbundler
from ..resource.resource_type import ResourceType
from ..resource.resource_type_producer import resource_type_producer
from ..resource.python_module import PythonModuleResourceType, python_module_pyobj
from .htypes.python_module import python_module_t
from ..resource.resource_registry import ResourceRegistry
from ..resource.resource_module import ResourceModule, load_resource_modules, load_resource_modules_list
from .htypes.legacy_type import legacy_type_t
from ..resource.legacy_type import (
    add_builtin_types_to_pyobj_cache,
    convert_builtin_types_to_dict,
    load_legacy_type_resources,
    legacy_type_pyobj,
    )
from .htypes.builtin_service import builtin_service_t
from ..resource.builtin_service import (
    add_builtin_services_to_pyobj_cache,
    builtin_service_pyobj,
    make_builtin_service_resource_module,
    )
from .htypes.attribute import attribute_t
from ..resource.attribute import AttributeResourceType, attribute_pyobj
from .htypes.call import call_t
from ..resource.call import CallResourceType, call_pyobj

log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'
HYPERAPP_DIR = Path(__file__).parent.parent.resolve()


class Services(object):

    builtin_services = [
        'services',
        'association_reg',
        'builtin_services',
        'builtin_types',
        'code_registry_ctr',
        'hyperapp_dir',
        'module_dir_list',
        'mosaic',
        'types',
        'web',
        'local_types',
        'type_module_loader',
        'on_stop',
        'stop_signal',
        'unbundler',
        'resource_type_factory',
        'resource_type_reg',
        'pyobj_creg',
        'resource_type_producer',
        'resource_registry_factory',
        'resource_registry',
        'resource_module_factory',
        'resource_loader',
        'resource_list_loader',
        'builtin_types_as_dict',
        'legacy_type_resource_loader',
        'builtin_service_resource_loader',
    ]

    def __init__(self, module_dir_list, additional_resource_dirs=None):
        self.hyperapp_dir = HYPERAPP_DIR
        self.resource_dir_list = [
            ResourceDir(HYPERAPP_DIR, module_dir_list),
            *(additional_resource_dirs or []),
            ]
        self.module_dir_list = module_dir_list
        self.on_stop = []
        self.stop_signal = threading.Event()
        self._is_stopped = False

    def init_services(self):
        log.info("Init services.")
        self.services = self  # Allows resources to access services itself.
        self.builtin_types = BuiltinTypeRegistry()
        self.types = TypeSystem()
        self.mosaic = Mosaic(self.types)
        self.web = Web(self.types, self.mosaic)
        self.types.init(self.builtin_types, self.mosaic, self.web)
        self.association_reg = AssociationRegistry()
        register_builtin_types(self.builtin_types, self.mosaic, self.types)
        self.local_types = {}  # module name -> name -> name_wrapped_mt ref.
        self.type_module_loader = TypeModuleLoader(self.builtin_types, self.mosaic, self.types)
        self.python_importer = PythonImporter()
        self.python_importer.register_meta_hook()
        self.resource_type_factory = partial(ResourceType, self.types, self.mosaic, self.web)
        self.resource_type_reg = {}  # resource_t -> ResourceType instance
        self.pyobj_creg = PyObjRegistry(self.mosaic, self.web, self.types, self.association_reg)
        self.unbundler = Unbundler(self.web, self.mosaic, self.association_reg)
        self.resource_type_producer = partial(resource_type_producer, self.resource_type_factory, self.resource_type_reg)
        self.resource_type_reg[python_module_t] = PythonModuleResourceType()
        self.pyobj_creg.register_actor(
            python_module_t, python_module_pyobj, self.mosaic, self.python_importer, self.pyobj_creg)
        self.resource_registry_factory = partial(ResourceRegistry, self.mosaic)
        self.resource_registry = self.resource_registry_factory()
        self.resource_module_factory = partial(
            ResourceModule,
            self.mosaic,
            self.resource_type_producer,
            self.pyobj_creg,
        )
        self.resource_loader = partial(
            load_resource_modules,
            self.resource_module_factory,
            )
        self.resource_list_loader = partial(
            load_resource_modules_list,
            self.resource_module_factory,
            )
        self.builtin_types_as_dict = partial(convert_builtin_types_to_dict, self.types, self.builtin_types)
        self.legacy_type_resource_loader = load_legacy_type_resources
        add_builtin_types_to_pyobj_cache(self.types, self.builtin_types, self.pyobj_creg)
        self.pyobj_creg.register_actor(legacy_type_t, legacy_type_pyobj, self.types)
        self.builtin_service_resource_loader = partial(
            make_builtin_service_resource_module, self.mosaic, self.builtin_services)
        self.resource_registry.set_module(
            'builtins', self.builtin_service_resource_loader(self.resource_registry))
        self.pyobj_creg.register_actor(builtin_service_t, builtin_service_pyobj, self)
        self.resource_type_reg[attribute_t] = AttributeResourceType()
        self.pyobj_creg.register_actor(attribute_t, attribute_pyobj, self.pyobj_creg)
        self.resource_type_reg[call_t] = CallResourceType()
        self.pyobj_creg.register_actor(call_t, call_pyobj, self.pyobj_creg)
        self.code_registry_ctr = partial(
            CodeRegistry, self.mosaic, self.web, self.types, self.association_reg, self.pyobj_creg)
        add_builtin_services_to_pyobj_cache(self, self.builtin_services, self.pyobj_creg)

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

    def load_type_modules(self):
        log.info("Load type modules.")
        self.type_module_loader.load_type_modules(self.module_dir_list, self.local_types)

    def unregister_import_meta_hook(self):
        self.python_importer.unregister_meta_hook()
