from pathlib import Path
import pytest

from hyperapp.common.code_module import code_module_t
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.code_module import register_code_module_types
from hyperapp.common.code_module_loader import CodeModuleLoader
from hyperapp.common.code_module_importer import CodeModuleImporter
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.visual_rep import pprint


pytest_plugins = ['hyperapp.common.htypes.test.fixtures']


TEST_DIR = Path(__file__).parent.resolve()


@pytest.fixture
def type_module_loader(builtin_types, mosaic, types):
    return TypeModuleLoader(builtin_types, mosaic, types)


@pytest.fixture
def local_type_module_registry(type_module_loader):
    return type_module_loader.registry


@pytest.fixture
def code_module_loader(mosaic, local_type_module_registry):
    return CodeModuleLoader(mosaic, local_type_module_registry)


def test_code_module_load(mosaic, type_module_loader, code_module_loader):
    type_module_loader.load_type_modules(TEST_DIR / 'test_type_modules')

    registry = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    for module_name, code_module_ref in registry.by_name.items():
        code_module = mosaic.resolve_ref(code_module_ref).value
        assert isinstance(code_module, code_module_t)
        pprint(code_module, title=f"Loaded code module: {module_name!r}")
    assert set(registry.by_name) == {
        'subdir.code_module_1',
        'code_module_2',
        }


@pytest.fixture
def code_module_importer(web, mosaic, types):
    importer = CodeModuleImporter(mosaic, types)
    importer.register_meta_hook()
    return importer


def test_code_module_import(mosaic, type_module_loader, code_module_loader, code_module_importer):
    type_module_loader.load_type_modules(TEST_DIR / 'test_type_modules')
    registry = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    code_module_importer.import_code_module(registry.by_requirement, registry.by_name['subdir.code_module_1'])


def test_code_module_import_from_code_module(mosaic, type_module_loader, code_module_loader, code_module_importer):
    type_module_loader.load_type_modules(TEST_DIR / 'test_type_modules')
    registry = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    code_module_importer.import_code_module(registry.by_requirement, registry.by_name['code_module_2'])


def test_require_code_module(mosaic, code_module_loader, code_module_importer):
    registry = code_module_loader.load_code_modules([TEST_DIR / 'test_require_code_modules'])
    code_module_importer.import_code_module(registry.by_requirement, registry.by_name['code_module_1'])
    assert len(code_module_importer.registry) == 2  # Both modules should be imported
