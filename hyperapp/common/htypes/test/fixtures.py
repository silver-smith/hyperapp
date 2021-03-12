import pytest

from hyperapp.common.htypes import BuiltinTypeRegistry, register_builtin_types
from hyperapp.common.code_module import register_code_module_types
from hyperapp.common.mosaic import Mosaic
from hyperapp.common.type_system import TypeSystem
from hyperapp.common.web import Web


@pytest.fixture
def web():
    return Web()


@pytest.fixture
def builtin_types():
    return BuiltinTypeRegistry()


@pytest.fixture
def types():
    return TypeSystem()


@pytest.fixture
def mosaic(web, builtin_types, types):
    mosaic = Mosaic(types)
    types.init(builtin_types, mosaic)
    web.add_source(mosaic)
    register_builtin_types(builtin_types, mosaic, types)
    register_code_module_types(builtin_types, mosaic, types)
    return mosaic

