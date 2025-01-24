import logging
import sys
from collections import namedtuple
from functools import partial
from pathlib import Path
from types import SimpleNamespace

from .htypes import BuiltinTypeRegistry, register_builtin_types
from .htypes.deduce_value_type import deduce_value_type
from .ref import ref_repr
from .mosaic import Mosaic
from .web import Web
from .type_module_loader import TypeModuleLoader
from .code_registry import CodeRegistry
from .cached_code_registry import CachedCodeRegistry
from .pyobj_registry import PyObjRegistry
from .association_registry import AssociationRegistry
from .python_importer import PythonImporter
from .unbundler import Unbundler
from .resource.resource_type import ResourceType
from .resource.resource_type_producer import resource_type_producer
from .resource.python_module import PythonModuleResourceType, python_module_pyobj
from .htypes.python_module import python_module_t
from .resource.resource_module import ResourceModule, load_resource_modules, load_resource_modules_list
from .project import BuiltinsProject, Project, load_projects_from_file
from .resource.legacy_type import (
    add_builtin_types_to_pyobj_cache,
    add_legacy_types_to_cache,
    convert_builtin_types_to_dict,
    load_legacy_type_resources,
    )
from .htypes.builtin_service import builtin_service_t
from .resource.builtin_service import (
    add_builtin_services_to_pyobj_cache,
    builtin_service_pyobj,
    make_builtin_service_resource_module,
    )
from .htypes.attribute import attribute_t
from .resource.attribute import AttributeResourceType, attribute_pyobj
from .htypes.call import call_t
from .resource.call import CallResourceType, call_pyobj
from .htypes.partial import partial_t
from .resource.partial import PartialResourceType, partial_pyobj
from .htypes.raw import raw_t
from .resource.raw import RawResourceType, raw_pyobj

log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'
HYPERAPP_DIR = Path(__file__).parent.parent.resolve()

pyobj_config = {
    }


class Services(object):

    builtin_services = [
        'services',
        'association_reg',
        'reconstructors',
        'builtin_services',
        'builtin_types',
        'cached_code_registry_ctr',
        'code_registry_ctr',
        'hyperapp_dir',
        'mosaic',
        'web',
        'type_module_loader',
        'on_stop',
        'unbundler',
        'resource_type_factory',
        'resource_type_reg',
        'pyobj_creg',
        'resource_type_producer',
        'resource_module_factory',
        'resource_loader',
        'resource_list_loader',
        'builtin_types_as_dict',
        'builtin_service_resource_loader',
        'deduce_t',
        'project_factory',
        'load_projects_from_file',
    ]

    def __init__(self):
        self.hyperapp_dir = HYPERAPP_DIR
        self.on_stop = []
        self._is_stopped = False

    def init_services(self):
        log.info("Init services.")
        self.services = self  # Allows resources to access services itself.
        self.builtin_types = BuiltinTypeRegistry()
        self.association_reg = AssociationRegistry()
        self.reconstructors = []
        self.pyobj_creg = PyObjRegistry(pyobj_config, self.reconstructors)
        self.mosaic = Mosaic(self.pyobj_creg)
        self.web = Web(self.mosaic, self.pyobj_creg)
        self.pyobj_creg.init(self.builtin_types, self.mosaic, self.web)
        register_builtin_types(self.builtin_types, self.pyobj_creg)
        self.type_module_loader = TypeModuleLoader(self.builtin_types, self.mosaic, self.pyobj_creg)
        self.python_importer = PythonImporter()
        self.python_importer.register_meta_hook()
        self.resource_type_factory = partial(ResourceType, self.mosaic, self.web, self.pyobj_creg)
        self.resource_type_reg = {}  # resource_t -> ResourceType instance
        self.deduce_t = deduce_value_type
        self.unbundler = Unbundler(self.web, self.mosaic, self.association_reg)
        self.resource_type_producer = partial(resource_type_producer, self.resource_type_factory, self.resource_type_reg)
        self.resource_type_reg[python_module_t] = PythonModuleResourceType()
        self.pyobj_creg.register_actor(
            python_module_t, python_module_pyobj,
            mosaic=self.mosaic,
            python_importer=self.python_importer,
            pyobj_creg=self.pyobj_creg,
            )
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
        self.builtin_types_as_dict = partial(convert_builtin_types_to_dict, self.pyobj_creg, self.builtin_types)
        add_builtin_types_to_pyobj_cache(self.pyobj_creg, self.builtin_types)
        self.builtin_service_resource_loader = partial(
            make_builtin_service_resource_module, self.mosaic, self.builtin_services)
        self.pyobj_creg.register_actor(builtin_service_t, builtin_service_pyobj, services=self)
        self.resource_type_reg[attribute_t] = AttributeResourceType()
        self.pyobj_creg.register_actor(attribute_t, attribute_pyobj, pyobj_creg=self.pyobj_creg)
        self.resource_type_reg[call_t] = CallResourceType()
        self.pyobj_creg.register_actor(call_t, call_pyobj, pyobj_creg=self.pyobj_creg)
        self.resource_type_reg[partial_t] = PartialResourceType()
        self.pyobj_creg.register_actor(partial_t, partial_pyobj, pyobj_creg=self.pyobj_creg)
        self.resource_type_reg[raw_t] = RawResourceType()
        self.pyobj_creg.register_actor(raw_t, raw_pyobj, web=self.web)
        self.code_registry_ctr = partial(CodeRegistry, self.web)
        self.cached_code_registry_ctr = partial(CachedCodeRegistry, self.mosaic, self.web)
        builtin_type_modules = load_legacy_type_resources(self.builtin_types_as_dict())
        builtins_project = BuiltinsProject(
            self.builtin_types_as_dict(), builtin_type_modules, self.builtin_service_resource_loader)
        self.project_factory = partial(Project, builtins_project, self.type_module_loader, self.resource_module_factory)
        self.load_projects_from_file = partial(load_projects_from_file, self.project_factory)
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

    def unregister_import_meta_hook(self):
        self.python_importer.unregister_meta_hook()
