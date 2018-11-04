from pathlib import Path

from hyperapp.common.htypes import make_root_type_namespace, code_module_t
from hyperapp.common.type_module import LocalTypeModuleRegistry
from hyperapp.common.builtin_types_registry import make_builtin_types_registry
from hyperapp.common.ref_registry import RefRegistry
from hyperapp.common.type_module_loader import TypeModuleLoader
from hyperapp.common.code_module_loader import CodeModuleLoader
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.visual_rep import pprint


TEST_MODULES_DIR = Path(__file__).parent.resolve()


def test_code_module_load():
    types = make_root_type_namespace()
    builtin_types_registry = make_builtin_types_registry()
    local_type_module_registry = LocalTypeModuleRegistry()
    ref_registry = RefRegistry(types)
    loader = TypeModuleLoader(types.builtins, builtin_types_registry, ref_registry, local_type_module_registry)
    loader.load_type_module('test_module_1', TEST_MODULES_DIR / 'test_module_1.types')
    loader.load_type_module('test_module_2', TEST_MODULES_DIR / 'test_module_2.types')

    loader = CodeModuleLoader(local_type_module_registry)
    code_module = loader.load_code_module('code_module_1', TEST_MODULES_DIR / 'code_module_1')
    assert isinstance(code_module, code_module_t)
    pprint(code_module, title='Loaded code module')
