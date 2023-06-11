import logging
from functools import partial
from types import SimpleNamespace

import pytest

from hyperapp.common.services import HYPERAPP_DIR
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.test.hyper_types_namespace import HyperTypesNamespace
from hyperapp.resource.resource_type import ResourceType

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
