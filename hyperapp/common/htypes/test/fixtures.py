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
def mosaic_and_web(builtin_types, types):
    mosaic = Mosaic(types)
    web = Web(types, mosaic)
    types.init(builtin_types, mosaic, web)
    register_builtin_types(builtin_types, mosaic, types)
    return (mosaic, web)


@pytest.fixture
def mosaic(mosaic_and_web):
    mosaic, web = mosaic_and_web
    return mosaic


@pytest.fixture
def web(mosaic_and_web):
    mosaic, web = mosaic_and_web
    return web
