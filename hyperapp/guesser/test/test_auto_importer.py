import logging
import tempfile
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def module_dir_list(hyperapp_dir, default_module_dir_list):
    return [
        *default_module_dir_list,
        hyperapp_dir / 'guesser',
        ]


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
        'transport.rsa_identity',
        'sync.transport.endpoint',
        'sync.rpc.rpc_endpoint',
        ]


@pytest.fixture
def subprocess(services):

    identity = services.generate_rsa_identity(fast=True)
    rpc_endpoint = services.rpc_endpoint_factory()
    services.endpoint_registry.register(identity, rpc_endpoint)

    module = services.resource_module_registry['sync.subprocess_context']
    subprocess_running_res = module['subprocess_running']
    subprocess_running = services.python_object_creg.animate(subprocess_running_res)

    with subprocess_running(services.module_dir_list, rpc_endpoint, identity, 'auto_importer') as process:
        yield process


def test_auto_importer(services, htypes, subprocess):

    resource_module = services.resource_module_factory(
        services.resource_module_registry,
        'test_auto_importer',
        Path(tempfile.gettempdir()) / 'test_auto_importer.resources.yaml',
        load_from_file=False,
    )

    auto_importer_module_path = Path(__file__).parent / 'test_resources' / 'auto_importer_module.dyn.py'
    module_res_t = services.resource_type_producer(htypes.python_module.python_module)
    import_rec_def_t = module_res_t.definition_t.fields['import_list'].element_t
    module_def = module_res_t.definition_t(
        module_name='auto_importer_module',
        file_name=str(auto_importer_module_path),
        import_list=[
            import_rec_def_t('*', 'guesser.auto_importer.auto_importer_loader'),
            ],
        )
    module_res_name = 'auto_importer_module'
    resource_module.set_definition(module_res_name, module_res_t, module_def)
    resource_module.add_import('guesser.auto_importer.auto_importer_loader')
    module = resource_module[module_res_name]
    module_ref = services.mosaic.put(module)

    runner_module = services.resource_module_registry['guesser.runner']
    runner_method_collect_attributes_res = runner_module['runner_method_collect_attributes']
    runner_method_collect_attributes_ref = services.mosaic.put(runner_method_collect_attributes_res)

    collect_attributes_call = subprocess.rpc_call(runner_method_collect_attributes_ref)
    global_list = collect_attributes_call(module_ref)
    log.info("Collected global list: %s", global_list)

    auto_importer_module = services.resource_module_registry['guesser.auto_importer']
    auto_importer_imports_res = auto_importer_module['auto_importer_imports_fn']
    auto_importer_imports_ref = services.mosaic.put(auto_importer_imports_res)
    auto_importer_imports_call = subprocess.rpc_call(auto_importer_imports_ref)
    imports = auto_importer_imports_call()
    log.info("Import list: %s", imports)

    assert imports == (
        htypes.auto_importer.import_rec('htypes.impl.list_spec', 'legacy_type.impl.list_spec'),
        htypes.auto_importer.import_rec('lcs', 'legacy_module.common.lcs'),
        htypes.auto_importer.import_rec('meta_registry', 'legacy_module.common.meta_registry'),
        htypes.auto_importer.import_rec('qt_keys', 'legacy_module.async.ui.qt.qt_keys'),
        htypes.auto_importer.import_rec('services.file_bundle', 'legacy_service.file_bundle'),
        htypes.auto_importer.import_rec('services.web', 'legacy_service.web'),
       )

    for r in imports:
        if '.' in r.resource_name:
            resource_module.add_import(r.resource_name)
    module_def = module_res_t.definition_t(
        module_name='check_importer_module',
        file_name=str(auto_importer_module_path),
        import_list=[
            import_rec_def_t(r.name, r.resource_name)
            for r in imports
            ],
        )
    check_module_res_name = 'check_importer_module'
    resource_module.set_definition(check_module_res_name, module_res_t, module_def)
    check_module = resource_module[check_module_res_name]
    check_module_ref = services.mosaic.put(check_module)

    check_global_list = collect_attributes_call(check_module_ref)
    log.info("Collected global list: %s", check_global_list)
    assert check_global_list == global_list
