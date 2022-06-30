from pathlib import Path
import pytest

from hyperapp.common.code_module import code_module_t
from hyperapp.common.code_module_loader import CodeModuleRegistry, CodeModuleLoader
from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module_registry import CodeModule, ModuleRegistry
from hyperapp.common.python_importer import PythonImporter
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.visual_rep import pprint
from hyperapp.common import cdr_coders  # register codec


pytest_plugins = [
    'hyperapp.common.test.services',
    'hyperapp.common.htypes.test.fixtures',
    ]

TEST_DIR = Path(__file__).parent.resolve()


@pytest.fixture
def local_types():
    return {}


@pytest.fixture
def local_modules():
    return CodeModuleRegistry()


@pytest.fixture
def type_module_loader(builtin_types, mosaic, types):
    return TypeModuleLoader(builtin_types, mosaic, types)


@pytest.fixture
def code_module_loader(hyperapp_dir, mosaic):
    return CodeModuleLoader(hyperapp_dir, mosaic)


def test_code_module_load(local_types, local_modules, type_module_loader, code_module_loader):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'], local_types)

    code_module_loader.load_code_modules(local_types, [TEST_DIR / 'test_code_modules'], local_modules)
    for module_name, code_module in local_modules.by_name.items():
        assert isinstance(code_module, code_module_t)
        pprint(code_module, title=f"Loaded code module: {module_name!r}")
    assert set(local_modules.by_name) == {
        'common.test.test_code_modules.module',
        'common.test.test_code_modules.module_with_types',
        'common.test.test_code_modules.module_requirements_main',
        'common.test.test_code_modules.subdir.module_requirements_sub',
        'common.test.test_code_modules.import_from_code_module_main',
        'common.test.test_code_modules.subdir.import_from_code_module_sub',
        'common.test.test_code_modules.module_init',
        }


@pytest.fixture
def python_importer():
    python_importer = PythonImporter()
    python_importer.register_meta_hook()
    yield python_importer
    python_importer.unregister_meta_hook()
    python_importer.remove_modules()


@pytest.fixture
def module_registry(mosaic, web, types, python_importer):
    module_code_registry = CodeRegistry('module', web, types)
    module_code_registry.register_actor(code_module_t, CodeModule.from_piece, types, web)
    on_start = []
    return ModuleRegistry(mosaic, web, python_importer, module_code_registry, on_start)


@pytest.fixture
def services():
    return None


def test_code_module_import(local_types, local_modules, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'], local_types)
    code_module_loader.load_code_modules(local_types, [TEST_DIR / 'test_code_modules'], local_modules)
    module = local_modules.by_name['common.test.test_code_modules.module']
    module_registry.import_module_list(services, [module], local_modules.by_requirement, {})
    python_module = module_registry.get_python_module(module)
    assert python_module.value == "Value in module"


def test_code_module_import_with_types(local_types, local_modules, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'], local_types)
    code_module_loader.load_code_modules(local_types, [TEST_DIR / 'test_code_modules'], local_modules)
    module = local_modules.by_name['common.test.test_code_modules.module_with_types']
    module_registry.import_module_list(services, [module], local_modules.by_requirement, {})
    python_module = module_registry.get_python_module(module)


def test_module_requirement(local_types, local_modules, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'], local_types)
    code_module_loader.load_code_modules(local_types, [TEST_DIR / 'test_code_modules'], local_modules)
    module_main = local_modules.by_name['common.test.test_code_modules.module_requirements_main']
    module_registry.import_module_list(services, [module_main], local_modules.by_requirement, {})
    module_sub = local_modules.by_name['common.test.test_code_modules.subdir.module_requirements_sub']
    assert module_registry.get_python_module(module_sub)  # Should be loaded too because it is required by module main.


def test_code_module_import_from_code_module(local_types, local_modules, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'], local_types)
    code_module_loader.load_code_modules(local_types, [TEST_DIR / 'test_code_modules'], local_modules)
    module_main = local_modules.by_name['common.test.test_code_modules.import_from_code_module_main']
    module_registry.import_module_list(services, [module_main], local_modules.by_requirement, {})
    module_sub = local_modules.by_name['common.test.test_code_modules.subdir.import_from_code_module_sub']
    assert module_registry.get_python_module(module_sub)  # Should be loaded too because it is required by module main.
    module_registry.get_python_module(module_main).main_value == 'main:sub'

 
def test_module_init(local_types, local_modules, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'], local_types)
    code_module_loader.load_code_modules(local_types, [TEST_DIR / 'test_code_modules'], local_modules)
    module = local_modules.by_name['common.test.test_code_modules.module_init']
    config = {'common.test.test_code_modules.module_init': {'value': 123}}
    module_registry.import_module_list(services, [module], local_modules.by_requirement, config)
    python_module = module_registry.get_python_module(module)
    assert python_module.this_module.value == 123


def test_enum_method(local_types, local_modules, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'], local_types)
    code_module_loader.load_code_modules(local_types, [TEST_DIR / 'test_code_modules'], local_modules)
    module = local_modules.by_name['common.test.test_code_modules.module_init']
    config = {'common.test.test_code_modules.module_init': {'value': 123}}
    module_registry.import_module_list(services, [module], local_modules.by_requirement, config)
    for module_name, method in module_registry.enum_method('some_method'):
        assert module_name == 'common.test.test_code_modules.module_init'
        assert method() == 456
        break
    else:
        pytest.fail("some_method is not returned by enum_method")


def test_init_phases(local_types, local_modules, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'], local_types)
    code_module_loader.load_code_modules(local_types, [TEST_DIR / 'test_code_modules'], local_modules)
    module = local_modules.by_name['common.test.test_code_modules.module_init']
    config = {'common.test.test_code_modules.module_init': {'value': 1}}
    module_registry.import_module_list(services, [module], local_modules.by_requirement, config)
    python_module = module_registry.get_python_module(module)
    assert python_module.this_module.phased_value == 3
