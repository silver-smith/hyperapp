from functools import partial

import pytest

from hyperapp.boot.htypes.python_module import python_module_t
from hyperapp.boot.htypes.attribute import attribute_t
from hyperapp.boot.htypes.call import call_t
from hyperapp.boot.htypes.partial import partial_t
from hyperapp.boot.resource.resource_type import ResourceType
from hyperapp.boot.resource.builtin_service import make_builtin_service_resource_module
from hyperapp.boot.resource.legacy_type import add_legacy_types_to_cache, load_legacy_type_resources
from hyperapp.boot.resource.resource_type_producer import resource_type_producer as resource_type_producer_fn
from hyperapp.boot.resource.resource_module import ResourceModule
from hyperapp.boot.resource.python_module import PythonModuleResourceType
from hyperapp.boot.resource.attribute import AttributeResourceType
from hyperapp.boot.resource.call import CallResourceType
from hyperapp.boot.resource.partial import PartialResourceType
from hyperapp.boot.resource.legacy_type import convert_builtin_types_to_dict
from hyperapp.boot.project import BuiltinsProject, Project, load_texts
from hyperapp.boot.test.hyper_types_namespace import HyperTypesNamespace


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
def project(
        type_module_loader, resource_module_factory, builtin_types_as_dict, builtin_service_resource_loader,
        test_resources_dir):
    builtin_type_modules = load_legacy_type_resources(builtin_types_as_dict())
    builtins_project = BuiltinsProject(builtin_types_as_dict(), builtin_type_modules, builtin_service_resource_loader)
    project = Project(
        builtins_project, type_module_loader, resource_module_factory,
        test_resources_dir, name='test-project')
    path_to_text = load_texts(test_resources_dir)
    project.load(path_to_text)
    return project


@pytest.fixture
def resource_registry(project):
    return project


@pytest.fixture
def htypes(pyobj_creg, project):
    return HyperTypesNamespace(pyobj_creg, project.types)
