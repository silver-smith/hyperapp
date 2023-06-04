import logging
from contextlib import contextmanager
from pathlib import Path

from . import htypes
from .services import (
    endpoint_registry,
    generate_rsa_identity,
    module_dir_list,
    mosaic,
    python_object_creg,
    rpc_endpoint_factory,
    types,
    web,
    )
from .code.subprocess_context import subprocess_running
from .code.runner import collect_attributes

log = logging.getLogger(__name__)


TEST_DIR = Path(__file__).parent.resolve()
TEST_RESOURCES_DIR = TEST_DIR / 'test_resources'

process_code_module_list = [
    'common.lcs_service',
    'ui.impl_registry',
    ]


@contextmanager
def process_running():
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)

    with subprocess_running(
            module_dir_list,
            process_code_module_list,
            rpc_endpoint,
            identity,
            'import_recorder',
            ) as process:
        yield process


def test_import_recorder():

    sample_rec_ref = types.reverse_resolve(htypes.sample_types.sample_rec)
    sample_rec_res = htypes.builtin.legacy_type(sample_rec_ref)
    sample_rec_res_ref = mosaic.put(sample_rec_res)
    another_rec_ref = types.reverse_resolve(htypes.sample_types.another_rec)
    another_rec_res = htypes.builtin.legacy_type(another_rec_ref)
    another_rec_res_ref = mosaic.put(another_rec_res)

    resources = [
        htypes.import_recorder.resource(('htypes', 'sample_types', 'sample_rec'), sample_rec_res_ref),
        htypes.import_recorder.resource(('htypes', 'sample_types', 'another_rec'), another_rec_res_ref),
        ]
    import_recorder_res = htypes.import_recorder.import_recorder(resources)
    import_recorder_ref = mosaic.put(import_recorder_res)

    sample_module_path = TEST_RESOURCES_DIR / 'import_recorder_sample_module.dyn.py'
    module_res = htypes.builtin.python_module(
        module_name='import_recorder_sample_module',
        source=sample_module_path.read_text(),
        file_path=str(sample_module_path),
        import_list=[
            htypes.builtin.import_rec('*', import_recorder_ref),
            ],
        )
    module_ref = mosaic.put(module_res)

    collect_attributes_res = python_object_creg.reverse_resolve(collect_attributes)
    collect_attributes_ref = mosaic.put(collect_attributes_res)

    with process_running() as process:

        collect_attributes_rpc = process.rpc_call(collect_attributes_ref)
        collected = collect_attributes_rpc(object_ref=module_ref)
        global_list = [web.summon(ref).name for ref in collected.attr_list]
        log.info("Collected global list: %s", global_list)

        import_recorder = process.proxy(import_recorder_ref)
        imports = import_recorder.used_imports()
        log.info("Import list: %s", imports)

        assert imports == (
            ('htypes', 'sample_types', 'another_rec'),
            ('htypes', 'sample_types', 'sample_rec'),
           )


def test_import_discoverer():

    import_discoverer_res = htypes.import_discoverer.import_discoverer()
    import_discoverer_ref = mosaic.put(import_discoverer_res)

    sample_module_path = TEST_RESOURCES_DIR / 'import_discoverer_sample_module.dyn.py'
    module_res = htypes.builtin.python_module(
        module_name='import_discoverer_sample_module',
        source=sample_module_path.read_text(),
        file_path=str(sample_module_path),
        import_list=[
            htypes.builtin.import_rec('*', import_discoverer_ref),
            ],
        )
    module_ref = mosaic.put(module_res)

    collect_attributes_res = python_object_creg.reverse_resolve(collect_attributes)
    collect_attributes_ref = mosaic.put(collect_attributes_res)

    with process_running() as process:

        collect_attributes_rpc = process.rpc_call(collect_attributes_ref)
        collected = collect_attributes_rpc(object_ref=module_ref)
        global_list = [web.summon(ref).name for ref in collected.attr_list]
        log.info("Collected global list: %s", global_list)

        import_discoverer = process.proxy(import_discoverer_ref)
        imports = import_discoverer.discovered_imports()
        log.info("Import list: %s", imports)

        assert imports == tuple(sorted([
            ('code',),
            ('code', 'code_module_1'),
            ('code', 'code_module_1', 'attr'),
            ('code', 'code_module_2'),
            ('services',),
            ('services', 'service_1'),
            ('services', 'service_2'),
            ('services', 'service_1', 'attr'),
            ('services', 'service_1', 'attr', 'nested'),
            ('tested',),
            ('tested', 'code'),
            ('tested', 'code', 'code_module_3'),
            ('tested', 'code', 'code_module_3', 'tested_attr'),
           ]))


def test_combined():

    sample_rec_ref = types.reverse_resolve(htypes.sample_types.sample_rec)
    sample_rec_res = htypes.builtin.legacy_type(sample_rec_ref)
    sample_rec_res_ref = mosaic.put(sample_rec_res)

    resources = [
        htypes.import_recorder.resource(('htypes', 'sample_types', 'sample_rec'), sample_rec_res_ref),
        ]
    import_recorder_res = htypes.import_recorder.import_recorder(resources)
    import_recorder_ref = mosaic.put(import_recorder_res)

    import_discoverer_res = htypes.import_discoverer.import_discoverer()
    import_discoverer_ref = mosaic.put(import_discoverer_res)

    sample_module_path = TEST_RESOURCES_DIR / 'import_both_sample_module.dyn.py'
    module_res = htypes.builtin.python_module(
        module_name='import_both_sample_module',
        source=sample_module_path.read_text(),
        file_path=str(sample_module_path),
        import_list=[
            htypes.builtin.import_rec('htypes.*', import_recorder_ref),
            htypes.builtin.import_rec('*', import_discoverer_ref),
            ],
        )
    module_ref = mosaic.put(module_res)

    collect_attributes_res = python_object_creg.reverse_resolve(collect_attributes)
    collect_attributes_ref = mosaic.put(collect_attributes_res)

    with process_running() as process:

        collect_attributes_rpc = process.rpc_call(collect_attributes_ref)
        collected = collect_attributes_rpc(object_ref=module_ref)
        global_list = [web.summon(ref).name for ref in collected.attr_list]
        log.info("Collected global list: %s", global_list)

        import_recorder = process.proxy(import_recorder_ref)
        recorded_imports = import_recorder.used_imports()
        log.info("Recorded import list: %s", recorded_imports)

        import_discoverer = process.proxy(import_discoverer_ref)
        discovered_imports = import_discoverer.discovered_imports()
        log.info("Discovered import list: %s", discovered_imports)

        assert recorded_imports == (
            ('htypes', 'sample_types', 'sample_rec'),
           )

        assert discovered_imports == tuple(sorted([
            ('code',),
            ('code', 'code_module_1'),
            ('code', 'code_module_1', 'attr'),
            ('code', 'code_module_2'),
            ('services',),
            ('services', 'service_1'),
            ('services', 'service_2'),
            ('services', 'service_1', 'attr'),
            ('services', 'service_1', 'attr', 'nested'),
            ('tested',),
            ('tested', 'code'),
            ('tested', 'code', 'code_module_3'),
            ('tested', 'code', 'code_module_3', 'tested_attr'),
           ]))
