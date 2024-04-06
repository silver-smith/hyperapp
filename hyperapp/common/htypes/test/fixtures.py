import pytest

from hyperapp.common.htypes import BuiltinTypeRegistry, register_builtin_types
from hyperapp.common.mosaic import Mosaic
from hyperapp.common.type_system import TypeSystem
from hyperapp.common.web import Web


@pytest.fixture
def builtin_types():
    return BuiltinTypeRegistry()


@pytest.fixture
def types():
    return TypeSystem()


@pytest.fixture
def web(types):
    return Web(types)


@pytest.fixture
def mosaic(web, builtin_types, types):
    mosaic = Mosaic(types)
    types.init(builtin_types, mosaic, web)
    web.add_source(mosaic)
    register_builtin_types(builtin_types, mosaic, types)
    return mosaic
