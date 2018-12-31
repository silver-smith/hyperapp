from pathlib import Path
import pytest

from hyperapp.common.htypes import register_builtin_types
from hyperapp.common.local_type_module import LocalTypeModuleRegistry
from hyperapp.common.code_module import code_module_t
from hyperapp.common.builtin_types_registry import make_builtin_types_registry
from hyperapp.common.ref_registry import RefRegistry
from hyperapp.common.ref_resolver import RefResolver
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.type_resolver import TypeResolver
from hyperapp.common.code_module import LocalCodeModuleRegistry, register_code_module_types
from hyperapp.common.code_module_loader import CodeModuleLoader
from hyperapp.common.code_module_importer import CodeModuleImporter
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.visual_rep import pprint


TEST_MODULES_DIR = Path(__file__).parent.resolve()



@pytest.fixture
def ref_resolver():
    return RefResolver()


@pytest.fixture
def type_resolver(ref_resolver):
    return TypeResolver(ref_resolver)


@pytest.fixture
def ref_registry(ref_resolver, type_resolver):
    registry = RefRegistry(type_resolver)
    register_builtin_types(registry, type_resolver)
    register_code_module_types(registry, type_resolver)
    ref_resolver.add_source(registry)
    return registry


@pytest.fixture
def local_type_module_registry():
    return LocalTypeModuleRegistry()


@pytest.fixture
def local_code_module_registry():
    return LocalCodeModuleRegistry()


@pytest.fixture
def type_module_loader(type_resolver, ref_registry, local_type_module_registry):
    return TypeModuleLoader(type_resolver, ref_registry, local_type_module_registry)


@pytest.fixture
def code_module_loader(ref_registry, local_type_module_registry, local_code_module_registry):
    return CodeModuleLoader(ref_registry, local_type_module_registry, local_code_module_registry)


def test_code_module_load(type_module_loader, code_module_loader):
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')

    code_module = code_module_loader.load_code_module(TEST_MODULES_DIR / 'code_module_1')
    assert isinstance(code_module, code_module_t)
    pprint(code_module, title='Loaded code module')


@pytest.fixture
def code_module_importer(ref_resolver, type_resolver):
    importer = CodeModuleImporter(type_resolver)
    importer.register_meta_hook()
    return importer


def test_code_module_import(ref_registry, type_module_loader, code_module_loader, code_module_importer):
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')
    code_module = code_module_loader.load_code_module(TEST_MODULES_DIR / 'code_module_1')
    code_module_ref = ref_registry.register_object(code_module)
    code_module = code_module_importer.import_code_module(code_module_ref)


def test_code_module_import_from_code_module(ref_registry, type_module_loader, code_module_loader, code_module_importer):
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_1.types')
    type_module_loader.load_type_module(TEST_MODULES_DIR / 'type_module_2.types')
    code_module_1 = code_module_loader.load_code_module(TEST_MODULES_DIR / 'code_module_1')
    code_module_2 = code_module_loader.load_code_module(TEST_MODULES_DIR / 'code_module_2')
    code_module_1_ref = ref_registry.register_object(code_module_1)
    code_module_2_ref = ref_registry.register_object(code_module_2)

    code_module_1 = code_module_importer.import_code_module(code_module_1_ref)
    code_module_2 = code_module_importer.import_code_module(code_module_2_ref)
