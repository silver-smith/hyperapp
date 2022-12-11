import logging
import tempfile
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']

TEST_DIR = Path(__file__).parent
TEST_RESOURCES_DIR = TEST_DIR / 'test_resources'


@pytest.fixture
def module_dir_list(hyperapp_dir, default_module_dir_list):
    return [
        *default_module_dir_list,
        hyperapp_dir / 'guesser',
        TEST_RESOURCES_DIR,
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
    'resource.resource_module',
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
            'import_recorder',
    ) as process:
        yield process


def test_import_recorder(services, htypes, python_object, subprocess):
    mosaic = services.mosaic
    web = services.web
    types = services.types
    resource_registry = services.resource_registry

    sample_rec_ref = types.reverse_resolve(htypes.sample_types.sample_rec)
    sample_rec_res = htypes.legacy_type.type(sample_rec_ref)
    sample_rec_res_ref = mosaic.put(sample_rec_res)
    another_rec_ref = types.reverse_resolve(htypes.sample_types.another_rec)
    another_rec_res = htypes.legacy_type.type(another_rec_ref)
    another_rec_res_ref = mosaic.put(another_rec_res)

    resources = [
        htypes.import_recorder.resource(('htypes', 'sample_types', 'sample_rec'), sample_rec_res_ref),
        htypes.import_recorder.resource(('htypes', 'sample_types', 'another_rec'), another_rec_res_ref),
        ]
    import_recorder_res = htypes.import_recorder.import_recorder(resources)
    import_recorder_ref = mosaic.put(import_recorder_res)

    sample_module_path = TEST_RESOURCES_DIR / 'import_recorder_sample_module.dyn.py'
    module_res = htypes.python_module.python_module(
        module_name='import_recorder_sample_module',
        source=sample_module_path.read_text(),
        file_path=str(sample_module_path),
        import_list=[
            htypes.python_module.import_rec('*', import_recorder_ref),
            ],
        )
    module_ref = mosaic.put(module_res)

    collect_attributes_res = resource_registry['guesser.runner', 'collect_attributes']
    collect_attributes_ref = mosaic.put(collect_attributes_res)
    collect_attributes = subprocess.rpc_call(collect_attributes_ref)

    collected = collect_attributes(object_ref=module_ref)
    global_list = [web.summon(ref).name for ref in collected.attr_list]
    log.info("Collected global list: %s", global_list)

    import_recorder = subprocess.proxy(import_recorder_ref)
    imports = import_recorder.used_imports()
    log.info("Import list: %s", imports)

    assert imports == (
        ('htypes', 'sample_types', 'another_rec'),
        ('htypes', 'sample_types', 'sample_rec'),
       )


def test_import_discoverer(services, htypes, python_object, subprocess):
    mosaic = services.mosaic
    web = services.web
    resource_registry = services.resource_registry

    import_discoverer_res = htypes.import_discoverer.import_discoverer()
    import_discoverer_ref = mosaic.put(import_discoverer_res)

    sample_module_path = TEST_RESOURCES_DIR / 'import_discoverer_sample_module.dyn.py'
    module_res = htypes.python_module.python_module(
        module_name='import_discoverer_sample_module',
        source=sample_module_path.read_text(),
        file_path=str(sample_module_path),
        import_list=[
            htypes.python_module.import_rec('*', import_discoverer_ref),
            ],
        )
    module_ref = mosaic.put(module_res)

    collect_attributes_res = resource_registry['guesser.runner', 'collect_attributes']
    collect_attributes_ref = mosaic.put(collect_attributes_res)
    collect_attributes = subprocess.rpc_call(collect_attributes_ref)

    collected = collect_attributes(object_ref=module_ref)
    global_list = [web.summon(ref).name for ref in collected.attr_list]
    log.info("Collected global list: %s", global_list)

    import_discoverer = subprocess.proxy(import_discoverer_ref)
    imports = import_discoverer.discovered_imports()
    log.info("Import list: %s", imports)

    assert imports == tuple(sorted([
        ('code', 'code_module_1'),
        ('code', 'code_module_1', 'attr'),
        ('code', 'code_module_2'),
        ('services', 'service_1'),
        ('services', 'service_2'),
        ('services', 'service_1', 'attr'),
        ('services', 'service_1', 'attr', 'nested'),
        ('tested', 'code', 'code_module_3', 'tested_attr'),
       ]))
