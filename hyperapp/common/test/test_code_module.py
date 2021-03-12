from pathlib import Path
import pytest

from hyperapp.common.htypes import register_builtin_types
from hyperapp.common.local_type_module import LocalTypeModuleRegistry
from hyperapp.common.code_module import code_module_t
from hyperapp.common.mosaic import Mosaic
from hyperapp.common.web import Web
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.type_system import TypeSystem
from hyperapp.common.code_module import LocalCodeModuleRegistry, register_code_module_types
from hyperapp.common.code_module_loader import CodeModuleLoader
from hyperapp.common.code_module_importer import CodeModuleImporter
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.visual_rep import pprint

TEST_MODULES_DIR = Path(__file__).parent.resolve()


@pytest.fixture
def web():
    return Web()


@pytest.fixture
def types():
    return TypeSystem()


@pytest.fixture
def mosaic(web, types):
    mosaic = Mosaic(types)
    types.init_mosaic(mosaic)
    web.add_source(mosaic)
    register_builtin_types(types)
    register_code_module_types(types)
    return mosaic


@pytest.fixture
def local_type_module_registry():
    return LocalTypeModuleRegistry()


@pytest.fixture
def local_code_module_registry():
    return LocalCodeModuleRegistry()


@pytest.fixture
def type_module_loader(types, mosaic, local_type_module_registry):
    return TypeModuleLoader(types, mosaic, local_type_module_registry)


@pytest.fixture
def code_module_loader(mosaic, local_type_module_registry, local_code_module_registry):
    return CodeModuleLoader(mosaic, local_type_module_registry, local_code_module_registry)


def test_code_module_load(type_module_loader, code_module_loader):
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')

    code_module = code_module_loader.load_code_module(TEST_MODULES_DIR / 'code_module_1')
    assert isinstance(code_module, code_module_t)
    pprint(code_module, title='Loaded code module')


@pytest.fixture
def code_module_importer(web, mosaic, types):
    importer = CodeModuleImporter(mosaic, types)
    importer.register_meta_hook()
    return importer


def test_code_module_import(mosaic, type_module_loader, code_module_loader, code_module_importer):
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')
    code_module = code_module_loader.load_code_module(TEST_MODULES_DIR / 'code_module_1')
    code_module_ref = mosaic.put(code_module)
    code_module_importer.import_code_module(code_module_ref)


def test_code_module_import_from_code_module(mosaic, type_module_loader, code_module_loader, code_module_importer):
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')
    code_module_1 = code_module_loader.load_code_module(TEST_MODULES_DIR / 'code_module_1')
    code_module_2 = code_module_loader.load_code_module(TEST_MODULES_DIR / 'code_module_2')
    code_module_1_ref = mosaic.put(code_module_1)
    code_module_2_ref = mosaic.put(code_module_2)

    code_module_importer.import_code_module(code_module_1_ref)
    code_module_importer.import_code_module(code_module_2_ref)
