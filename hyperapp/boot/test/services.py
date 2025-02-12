import logging
from functools import partial

import pytest

from hyperapp.boot.htypes import BuiltinTypeRegistry, register_builtin_types
from hyperapp.boot.htypes.python_module import python_module_t
from hyperapp.boot.htypes.attribute import attribute_t
from hyperapp.boot.htypes.call import call_t
from hyperapp.boot.htypes.partial import partial_t
from hyperapp.boot.htypes.deduce_value_type import deduce_value_type
from hyperapp.boot.mosaic import Mosaic
from hyperapp.boot.web import Web
from hyperapp.boot.services import HYPERAPP_DIR, pyobj_config
from hyperapp.boot.code_registry import CodeRegistry
from hyperapp.boot.pyobj_registry import PyObjRegistry
from hyperapp.boot.association_registry import AssociationRegistry
from hyperapp.boot.python_importer import PythonImporter
from hyperapp.boot.type_module_loader import TypeModuleLoader
from hyperapp.boot.resource_dir import ResourceDir
from hyperapp.boot.test.hyper_types_namespace import HyperTypesNamespace
from hyperapp.boot.resource.resource_type import ResourceType
from hyperapp.boot.resource.resource_type_producer import resource_type_producer as resource_type_producer_fn
from hyperapp.boot.resource.resource_registry import ResourceRegistry
from hyperapp.boot.resource.resource_module import ResourceModule, load_resource_modules_list
from hyperapp.boot.resource.legacy_type import add_legacy_types_to_cache
from hyperapp.boot.resource.python_module import PythonModuleResourceType, python_module_pyobj
from hyperapp.boot.resource.attribute import AttributeResourceType, attribute_pyobj
from hyperapp.boot.resource.call import CallResourceType, call_pyobj
from hyperapp.boot.resource.partial import PartialResourceType, partial_pyobj
from hyperapp.boot.resource.legacy_type import convert_builtin_types_to_dict, load_legacy_type_resources
from hyperapp.boot.resource.builtin_service import builtin_service_pyobj, make_builtin_service_resource_module

log = logging.getLogger(__name__)


@pytest.fixture
def association_reg():
    return AssociationRegistry()


@pytest.fixture
def reconstructors():
    return []


@pytest.fixture
def pyobj_creg(reconstructors):
    return PyObjRegistry(pyobj_config, reconstructors)


@pytest.fixture
def builtin_types():
    return BuiltinTypeRegistry()


@pytest.fixture
def python_importer():
    importer = PythonImporter()
    importer.register_meta_hook()
    yield importer
    importer.remove_modules()
    importer.unregister_meta_hook()


@pytest.fixture
def mosaic_and_web(pyobj_creg, builtin_types, python_importer):
    mosaic = Mosaic(pyobj_creg)
    web = Web(mosaic, pyobj_creg)
    pyobj_creg.init(builtin_types, mosaic, web)
    register_builtin_types(builtin_types, pyobj_creg)
    pyobj_creg.register_actor(
        python_module_t, python_module_pyobj,
        mosaic=mosaic,
        python_importer=python_importer,
        pyobj_creg=pyobj_creg,
        )
    # pyobj_creg.register_actor(builtin_service_t, builtin_service_pyobj, self)
    pyobj_creg.register_actor(attribute_t, attribute_pyobj, pyobj_creg=pyobj_creg)
    pyobj_creg.register_actor(call_t, call_pyobj, pyobj_creg=pyobj_creg)
    pyobj_creg.register_actor(partial_t, partial_pyobj, pyobj_creg=pyobj_creg)
    return (mosaic, web)


@pytest.fixture
def mosaic(mosaic_and_web):
    mosaic, web = mosaic_and_web
    return mosaic


@pytest.fixture
def web(mosaic_and_web):
    mosaic, web = mosaic_and_web
    return web


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
def type_module_loader(builtin_types, mosaic, pyobj_creg):
    return TypeModuleLoader(builtin_types, mosaic, pyobj_creg)


@pytest.fixture
def local_types(type_module_loader, module_dir_list):
    lt = {}
    type_module_loader.load_type_modules(module_dir_list, lt)
    return lt


@pytest.fixture
def htypes(pyobj_creg, local_types):
    return HyperTypesNamespace(pyobj_creg, local_types)


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
def deduce_t(mosaic, pyobj_creg):
    return deduce_value_type


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
def code_registry_ctr(web):
    return partial(CodeRegistry, web)


@pytest.fixture
def builtin_services(
        mosaic,
        web,
        ):
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
