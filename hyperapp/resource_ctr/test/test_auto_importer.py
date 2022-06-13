import logging
import tempfile
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def code_module_list():
    return [
        'resource.resource_type',
        'resource.registry',
        'resource.resource_module',
        'resource.legacy_module',
        'resource.legacy_service',
        'resource.legacy_type',
        'resource.attribute',
        'resource.partial',
        'resource.call',
        'resource.list_service',
        'resource.live_list_service',
        'resource.tree_service',
        'resource.value',
        'resource.piece_ref',
        'resource.typed_piece',
        'resource.selector',
        'resource.rpc_command',
        'resource.rpc_callback',
        'resource.map_service',
        'resource.python_module',
        ]


@pytest.fixture
def subprocess(services):
    module = services.resource_module_registry['sync.subprocess_context']
    subprocess_running_res = module['subprocess_running']
    subprocess_running = services.python_object_creg.animate(subprocess_running_res)
    with subprocess_running('auto_importer') as process:
        yield process


def test_auto_importer(services, htypes, subprocess):

    resource_module = services.resource_module_factory(
        'test_auto_importer',
        Path(tempfile.gettempdir()) / 'test_auto_importer.resources.yaml',
        allow_missing=True,
    )

    auto_importer_module_path = Path(__file__).parent / 'test_resources' / 'auto_importer_module.dyn.py'
    module_res_t = services.resource_type_producer(htypes.python_module.python_module)
    import_rec_def_t = module_res_t.definition_t.fields['import_list'].element_t
    module_def = module_res_t.definition_t(
        module_name='auto_importer_module',
        file_name=str(auto_importer_module_path),
        import_list=[
            import_rec_def_t('*', 'resource_ctr.auto_importer.auto_importer_loader'),
            ],
        )
    module_res_name = 'auto_importer_module'
    resource_module.set_definition(module_res_name, module_res_t, module_def)
    resource_module.add_import('resource_ctr.auto_importer.auto_importer_loader')
    module = resource_module[module_res_name]
    module_ref = services.mosaic.put(module)

    runner_module = services.resource_module_registry['server.htest_runner']
    runner_method_collect_attributes_res = runner_module['runner_method_collect_attributes']
    runner_method_collect_attributes_ref = services.mosaic.put(runner_method_collect_attributes_res)

    collect_attributes_call = subprocess.rpc_call(runner_method_collect_attributes_ref)
    global_list = collect_attributes_call(module_ref)
    log.info("Collected global list: %s", global_list)

    auto_importer_module = services.resource_module_registry['resource_ctr.auto_importer']
    auto_importer_import_list_res = auto_importer_module['auto_importer_import_list_fn']
    auto_importer_import_list_ref = services.mosaic.put(auto_importer_import_list_res)
    auto_importer_import_list_call = subprocess.rpc_call(auto_importer_import_list_ref)
    import_list = auto_importer_import_list_call()
    log.info("Import list: %s", import_list)

    assert set(import_list) == {'services.web', 'htypes.impl.list_spec', 'meta_registry'}
