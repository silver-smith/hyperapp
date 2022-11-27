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


process_code_module_list = [
    'common.lcs',
    'common.lcs_service',
    'ui.impl_registry',
    'ui.global_command_list',
    'resource.register_associations',
    ]


@pytest.fixture
def python_object(services):
    resource_registry = services.resource_registry
    python_object_creg = services.python_object_creg

    def get(path):
        module_name, object_name = path.split(':')
        object_res = resource_registry[module_name, object_name]
        return python_object_creg.animate(object_res)

    return get


@pytest.fixture
def subprocess(services, python_object):

    identity = services.generate_rsa_identity(fast=True)
    rpc_endpoint = services.rpc_endpoint_factory()
    services.endpoint_registry.register(identity, rpc_endpoint)

    subprocess_running = python_object('sync.subprocess_context:subprocess_running')

    with subprocess_running(
            services.module_dir_list,
            process_code_module_list,
            rpc_endpoint,
            identity,
            'auto_importer',
    ) as process:
        yield process


def test_auto_importer(services, htypes, python_object, subprocess):

    CustomResources = python_object('guesser.custom_resource_module_registry:CustomResources')
    available_import_resources = python_object('guesser.import_resources:available_import_resources')

    custom_resources = CustomResources(
        types=services.local_types,
        modules=services.local_modules,
        res_module_reg=services.resource_registry,
        )
    import_resources = dict(available_import_resources(custom_resources))
    resources = [
        htypes.auto_importer.resource(import_name, rec.resource_ref)
        for import_name, rec in import_resources.items()
        ]
    auto_importer_res = htypes.auto_importer.auto_importer(resources)
    auto_importer_ref = services.mosaic.put(auto_importer_res)

    auto_importer_module_path = Path(__file__).parent / 'test_resources' / 'auto_importer_module.dyn.py'
    module_res = htypes.python_module.python_module(
        module_name='auto_importer_module',
        source=auto_importer_module_path.read_text(),
        file_path=str(auto_importer_module_path),
        import_list=[
            htypes.python_module.import_rec('*', auto_importer_ref),
            ],
        )
    module_ref = services.mosaic.put(module_res)

    collect_attributes_res = services.resource_registry['guesser.runner', 'collect_attributes']
    collect_attributes_ref = services.mosaic.put(collect_attributes_res)

    collect_attributes_call = subprocess.rpc_call(collect_attributes_ref)
    collected = collect_attributes_call(object_ref=module_ref)
    global_list = [services.web.summon(ref).name for ref in collected.attr_list]
    log.info("Collected global list: %s", global_list)

    auto_importer = subprocess.proxy(auto_importer_ref)
    imports = auto_importer.imports()
    log.info("Import list: %s", imports)

    assert imports == (
        'htypes.impl.list_spec',
        'lcs',
        'meta_registry',
        'qt_keys',
        'services.file_bundle',
        'services.web',
       )

    # Now, check if target module works with discovered imports.

    resource_module = services.resource_module_factory(
        services.resource_registry,
        'test_auto_importer',
        Path(tempfile.gettempdir()) / 'test_auto_importer.resources.yaml',
        load_from_file=False,
    )

    module_res_t = services.resource_type_producer(htypes.python_module.python_module)
    import_rec_def_t = module_res_t.definition_t.fields['import_list'].element_t

    import_to_res_name = {
        import_name: rec.resource_name
        for import_name, rec in import_resources.items()
        }
    import_list = []
    for name in imports:
        resource_name = import_to_res_name[name]
        resource_module.add_import(resource_name)
        import_list.append(import_rec_def_t(name, resource_name))
    module_def = module_res_t.definition_t(
        module_name='check_importer_module',
        file_name=str(auto_importer_module_path),
        import_list=import_list,
        )

    check_module_res_name = 'check_importer_module'
    resource_module.set_definition(check_module_res_name, module_res_t, module_def)
    check_module = resource_module[check_module_res_name]
    check_module_ref = services.mosaic.put(check_module)

    check_collected = collect_attributes_call(object_ref=check_module_ref)
    check_global_list = [services.web.summon(ref).name for ref in check_collected.attr_list]
    log.info("Collected global list: %s", check_global_list)
    assert check_global_list == global_list
