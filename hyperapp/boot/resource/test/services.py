from functools import partial

import pytest

from hyperapp.boot.htypes.python_module import python_module_t
from hyperapp.boot.htypes.attribute import attribute_t
from hyperapp.boot.htypes.call import call_t
from hyperapp.boot.htypes.partial import partial_t
from hyperapp.boot.resource.resource_type import ResourceType
from hyperapp.boot.resource.resource_registry import ResourceRegistry
from hyperapp.boot.resource.builtin_service import make_builtin_service_resource_module
from hyperapp.boot.resource.legacy_type import add_legacy_types_to_cache, load_legacy_type_resources
from hyperapp.boot.resource.resource_type_producer import resource_type_producer as resource_type_producer_fn
from hyperapp.boot.resource.resource_module import ResourceModule, load_resource_modules_list
from hyperapp.boot.resource.python_module import PythonModuleResourceType
from hyperapp.boot.resource.attribute import AttributeResourceType
from hyperapp.boot.resource.call import CallResourceType
from hyperapp.boot.resource.partial import PartialResourceType
from hyperapp.boot.resource.legacy_type import convert_builtin_types_to_dict


@pytest.fixture
def resource_type_factory(mosaic, web, pyobj_creg):
    return partial(ResourceType, mosaic, web, pyobj_creg)


@pytest.fixture
def resource_type_reg():
    reg = {}
    reg[python_module_t] = PythonModuleResourceType()
    reg[attribute_t] = AttributeResourceType()
    reg[call_t] = CallResourceType()
    reg[partial_t] = PartialResourceType()
    return reg


@pytest.fixture
def resource_type_producer(resource_type_factory, resource_type_reg):
    return partial(resource_type_producer_fn, resource_type_factory, resource_type_reg)


@pytest.fixture
def resource_module_factory(mosaic, resource_type_producer, pyobj_creg):
    return partial(ResourceModule, mosaic, resource_type_producer, pyobj_creg)


@pytest.fixture
def resource_list_loader(resource_module_factory):
    return partial(load_resource_modules_list, resource_module_factory)


@pytest.fixture
def builtin_types_as_dict(pyobj_creg, builtin_types):
    return partial(convert_builtin_types_to_dict, pyobj_creg, builtin_types)


@pytest.fixture
def builtin_services(mosaic, web):
    return {
        'mosaic': mosaic,
        'web': web,
        }


@pytest.fixture
def builtin_service_resource_loader(mosaic, builtin_services):
    return partial(make_builtin_service_resource_module, mosaic, builtin_services.keys())


@pytest.fixture
def resource_registry(
        resource_list_loader,
        builtin_types_as_dict,
        local_types,
        builtin_service_resource_loader,
        resource_dir_list,
        ):
    registry = ResourceRegistry()
    resource_list_loader(resource_dir_list, registry)
    legacy_type_modules = load_legacy_type_resources({**builtin_types_as_dict(), **local_types})
    registry.update_modules(legacy_type_modules)
    add_legacy_types_to_cache(registry, legacy_type_modules)  # Also adds builtin types, again.
    registry.set_module('builtins', builtin_service_resource_loader(registry))
    return registry
