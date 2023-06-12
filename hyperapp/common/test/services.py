import logging
from functools import partial
from types import SimpleNamespace

import pytest

from hyperapp.common.htypes.meta_association import meta_association
from hyperapp.common.htypes.python_module import python_module_t
from hyperapp.common.htypes.attribute import attribute_t
from hyperapp.common.htypes.legacy_type import legacy_type_t
from hyperapp.common.services import HYPERAPP_DIR
from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.cached_code_registry import CachedCodeRegistry
from hyperapp.common.association_registry import AssociationRegistry
from hyperapp.common.python_importer import PythonImporter
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.resource_dir import ResourceDir
from hyperapp.common.meta_association_type import MetaAssociationResourceType
from hyperapp.common.test.hyper_types_namespace import HyperTypesNamespace
from hyperapp.resource.resource_type import ResourceType
from hyperapp.resource.resource_type_producer import resource_type_producer as resource_type_producer_fn
from hyperapp.resource.resource_registry import ResourceRegistry
from hyperapp.resource.resource_module import ResourceModule, load_resource_modules_list
from hyperapp.resource.python_module import PythonModuleResourceType, python_module_pyobj
from hyperapp.resource.attribute import AttributeResourceType, attribute_pyobj
from hyperapp.resource.legacy_type import convert_builtin_types_to_dict, load_legacy_type_resources, legacy_type_pyobj
from hyperapp.resource.legacy_service import builtin_service_python_object, make_legacy_service_resource_module

log = logging.getLogger(__name__)


@pytest.fixture
def hyperapp_dir():
    return HYPERAPP_DIR


@pytest.fixture
def default_module_dir_list(hyperapp_dir):
    return [hyperapp_dir]


@pytest.fixture
def module_dir_list(default_module_dir_list):
    return default_module_dir_list


@pytest.fixture
def additional_resource_dirs():
    return []


@pytest.fixture
def resource_dir_list(hyperapp_dir, module_dir_list, additional_resource_dirs):
    return [
        ResourceDir(hyperapp_dir, module_dir_list),
        *[ResourceDir(d) for d in additional_resource_dirs],
        ]


@pytest.fixture
def meta_registry(web, types):
    return CodeRegistry('meta', web, types)


@pytest.fixture
def association_reg(meta_registry):
    return AssociationRegistry(meta_registry)


@pytest.fixture
def type_module_loader(builtin_types, mosaic, types):
    return TypeModuleLoader(builtin_types, mosaic, types)


@pytest.fixture
def local_types(type_module_loader, module_dir_list):
    lt = {}
    type_module_loader.load_type_modules(module_dir_list, lt)
    return lt


@pytest.fixture
def htypes(types, local_types):
    return HyperTypesNamespace(types, local_types)


@pytest.fixture
def resource_type_factory(types, mosaic, web):
    return partial(ResourceType, types, mosaic, web)


@pytest.fixture
def resource_type_reg():
    reg = {}
    reg[meta_association] = MetaAssociationResourceType()
    reg[python_module_t] = PythonModuleResourceType()
    reg[attribute_t] = AttributeResourceType()
    return reg


@pytest.fixture
def resource_type_producer(resource_type_factory, resource_type_reg):
    return partial(resource_type_producer_fn, resource_type_factory, resource_type_reg)


@pytest.fixture
def python_importer():
    importer = PythonImporter()
    importer.register_meta_hook()
    yield importer
    importer.remove_modules()
    importer.unregister_meta_hook()


@pytest.fixture
def python_object_creg(types, mosaic, web, python_importer):
    creg = CachedCodeRegistry('python_object', web, types)
    creg.register_actor(python_module_t, python_module_pyobj, mosaic, python_importer, creg)
    creg.register_actor(legacy_type_t, legacy_type_pyobj, types)
    return creg


@pytest.fixture
def resource_registry_factory(mosaic):
    return partial(ResourceRegistry, mosaic)


@pytest.fixture
def resource_module_factory(mosaic, resource_type_producer, python_object_creg):
    return partial(ResourceModule, mosaic, resource_type_producer, python_object_creg)


@pytest.fixture
def resource_list_loader(resource_module_factory):
    return partial(load_resource_modules_list, resource_module_factory)


@pytest.fixture
def legacy_type_resource_loader():
    return load_legacy_type_resources


@pytest.fixture
def builtin_types_as_dict(types, builtin_types):
    return partial(convert_builtin_types_to_dict, types, builtin_types)


@pytest.fixture
def aux_unbundler_hooks():
    return []


@pytest.fixture
def builtin_services(
        association_reg,
        builtin_types,
        hyperapp_dir,
        module_dir_list,
        mosaic,
        types,
        web,
        local_types,
        type_module_loader,
        # meta_registry,
        # on_stop,
        # stop_signal,
        aux_unbundler_hooks,
        # unbundler,
        resource_type_factory,
        resource_type_reg,
        python_object_creg,
        resource_type_producer,
        resource_registry_factory,
        # resource_registry,
        resource_module_factory,
        # resource_loader,
        resource_list_loader,
        builtin_types_as_dict,
        legacy_type_resource_loader,
        # legacy_service_resource_loader,
        ):
    return {
        'association_reg': association_reg,
        'builtin_types': builtin_types,
        'hyperapp_dir': hyperapp_dir,
        'module_dir_list': module_dir_list,
        'mosaic': mosaic,
        'types': types,
        'web': web,
        'local_types': local_types,
        'type_module_loader': type_module_loader,
        # 'meta_registry': meta_registry,
        # 'on_stop': on_stop,
        # 'stop_signal': stop_signal,
        'aux_unbundler_hooks': aux_unbundler_hooks,
        # 'unbundler': unbundler,
        'resource_type_factory': resource_type_factory,
        'resource_type_reg': resource_type_reg,
        'python_object_creg': python_object_creg,
        'resource_type_producer': resource_type_producer,
        'resource_registry_factory': resource_registry_factory,
        # 'resource_registry': resource_registry,
        'resource_module_factory': resource_module_factory,
        # 'resource_loader': resource_loader,
        'resource_list_loader': resource_list_loader,
        'builtin_types_as_dict': builtin_types_as_dict,
        'legacy_type_resource_loader': legacy_type_resource_loader,
        # 'legacy_service_resource_loader': legacy_service_resource_loader,
    }


@pytest.fixture
def legacy_service_resource_loader(mosaic, builtin_services):
    return partial(make_legacy_service_resource_module, mosaic, builtin_services.keys())


@pytest.fixture
def resource_registry(
        resource_registry_factory,
        resource_list_loader,
        legacy_type_resource_loader,
        builtin_types_as_dict,
        local_types,
        legacy_service_resource_loader,
        resource_dir_list,
        ):
    registry = resource_registry_factory()
    resource_list_loader(resource_dir_list, registry)
    registry.update_modules(legacy_type_resource_loader({**builtin_types_as_dict(), **local_types}))
    registry.set_module('legacy_service', legacy_service_resource_loader(registry))
    return registry
