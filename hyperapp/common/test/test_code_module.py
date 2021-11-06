from pathlib import Path
import pytest

from hyperapp.common.code_module import code_module_t
from hyperapp.common.code_module_loader import CodeModuleLoader
from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module_registry import CodeModule, ModuleRegistry
from hyperapp.common.python_importer import PythonImporter
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.visual_rep import pprint
from hyperapp.common import cdr_coders  # register codec


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
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'])

    registry = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    for module_name, code_module_ref in registry.by_name.items():
        code_module = mosaic.resolve_ref(code_module_ref).value
        assert isinstance(code_module, code_module_t)
        pprint(code_module, title=f"Loaded code module: {module_name!r}")
    assert set(registry.by_name) == {
        'module',
        'module_with_types',
        'module_requirements_main',
        'subdir.module_requirements_sub',
        'import_from_code_module_main',
        'subdir.import_from_code_module_sub',
        'module_init',
        }


@pytest.fixture
def python_importer():
    python_importer = PythonImporter()
    python_importer.register_meta_hook()
    yield python_importer
    python_importer.unregister_meta_hook()


@pytest.fixture
def module_registry(mosaic, web, types, python_importer):
    module_code_registry = CodeRegistry('module', web, types)
    module_code_registry.register_actor(code_module_t, CodeModule.from_piece, types, web)
    return ModuleRegistry(mosaic, web, python_importer, module_code_registry)


@pytest.fixture
def services():
    return None


def test_code_module_import(web, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'])
    local_modules = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    module = web.summon(local_modules.by_name['module'])
    module_registry.import_module_list(services, [module], local_modules.by_requirement, {})
    python_module = module_registry.get_python_module(module)
    assert python_module.value == "Value in module"


def test_code_module_import_with_types(web, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'])
    local_modules = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    module = web.summon(local_modules.by_name['module_with_types'])
    module_registry.import_module_list(services, [module], local_modules.by_requirement, {})
    python_module = module_registry.get_python_module(module)


def test_module_requirement(web, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'])
    local_modules = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    module_main = web.summon(local_modules.by_name['module_requirements_main'])
    module_registry.import_module_list(services, [module_main], local_modules.by_requirement, {})
    module_sub = web.summon(local_modules.by_name['subdir.module_requirements_sub'])
    assert module_registry.get_python_module(module_sub)  # Should be loaded too because it is required by module main.


def test_code_module_import_from_code_module(web, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'])
    local_modules = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    module_main = web.summon(local_modules.by_name['import_from_code_module_main'])
    module_registry.import_module_list(services, [module_main], local_modules.by_requirement, {})
    module_sub = web.summon(local_modules.by_name['subdir.import_from_code_module_sub'])
    assert module_registry.get_python_module(module_sub)  # Should be loaded too because it is required by module main.
    module_registry.get_python_module(module_main).main_value == 'main:sub'

 
def test_module_init(web, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'])
    local_modules = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    module = web.summon(local_modules.by_name['module_init'])
    config = {'module_init': {'value': 123}}
    module_registry.import_module_list(services, [module], local_modules.by_requirement, config)
    python_module = module_registry.get_python_module(module)
    assert python_module.this_module.value == 123


def test_enum_method(web, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'])
    local_modules = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    module = web.summon(local_modules.by_name['module_init'])
    config = {'module_init': {'value': 123}}
    module_registry.import_module_list(services, [module], local_modules.by_requirement, config)
    for module_name, method in module_registry.enum_method('some_method'):
        assert module_name == 'module_init'
        assert method() == 456
        break
    else:
        pytest.fail("some_method is not returned by enum_method")


def test_init_phases(web, type_module_loader, code_module_loader, module_registry, services):
    type_module_loader.load_type_modules([TEST_DIR / 'test_type_modules'])
    local_modules = code_module_loader.load_code_modules([TEST_DIR / 'test_code_modules'])
    module = web.summon(local_modules.by_name['module_init'])
    config = {'module_init': {'value': 1}}
    module_registry.import_module_list(services, [module], local_modules.by_requirement, config)
    python_module = module_registry.get_python_module(module)
    assert python_module.this_module.phased_value == 3
