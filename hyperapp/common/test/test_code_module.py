from pathlib import Path
import pytest

from hyperapp.common.htypes import make_root_type_namespace
from hyperapp.common.type_module import LocalTypeModuleRegistry
from hyperapp.common.code_module import code_module_t, make_code_module_namespace
from hyperapp.common.builtin_types_registry import make_builtin_types_registry
from hyperapp.common.ref_registry import RefRegistry
from hyperapp.common.ref_resolver import RefResolver
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.type_resolver import TypeResolver
from hyperapp.common.code_module_loader import CodeModuleLoader
from hyperapp.common.code_module_importer import CodeModuleImporter
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.visual_rep import pprint


TEST_MODULES_DIR = Path(__file__).parent.resolve()


@pytest.fixture
def types():
    ns = make_root_type_namespace()
    ns['code_module'] = make_code_module_namespace()
    return ns


@pytest.fixture
def ref_registry(types):
    return RefRegistry(types)


@pytest.fixture
def local_type_module_registry():
    return LocalTypeModuleRegistry()


@pytest.fixture
def type_module_loader(types, ref_registry, local_type_module_registry):
    builtin_types_registry = make_builtin_types_registry()
    return TypeModuleLoader(types.builtins, builtin_types_registry, ref_registry, local_type_module_registry)


@pytest.fixture
def code_module_loader(local_type_module_registry):
    return CodeModuleLoader(local_type_module_registry)


def test_code_module_load(type_module_loader, code_module_loader):
    type_module_loader.load_type_module('type_module_1', TEST_MODULES_DIR / 'type_module_1.types')
    type_module_loader.load_type_module('type_module_2', TEST_MODULES_DIR / 'type_module_2.types')

    code_module = code_module_loader.load_code_module('code_module_1', TEST_MODULES_DIR / 'code_module_1')
    assert isinstance(code_module, code_module_t)
    pprint(code_module, title='Loaded code module')


def test_code_module_import(types, ref_registry, type_module_loader, code_module_loader):
    type_module_loader.load_type_module('type_module_1', TEST_MODULES_DIR / 'type_module_1.types')
    type_module_loader.load_type_module('type_module_2', TEST_MODULES_DIR / 'type_module_2.types')
    code_module = code_module_loader.load_code_module('code_module_1', TEST_MODULES_DIR / 'code_module_1')
    code_module_ref = ref_registry.register_object(code_module)

    ref_resolver = RefResolver(types)
    ref_resolver.add_source(ref_registry)

    builtin_types_registry = make_builtin_types_registry()
    type_resolver = TypeResolver(types, builtin_types_registry, ref_resolver)

    code_module_importer = CodeModuleImporter(ref_resolver, type_resolver)
    code_module_importer.register_meta_hook()
    code_module = code_module_importer.import_code_module(code_module_ref)
