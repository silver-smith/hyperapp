import logging
import yaml
from pathlib import Path

from .services import (
    mosaic,
    resource_registry,
    )
from .code.rc import compile_resources

log = logging.getLogger(__name__)


TEST_DIR = Path(__file__).parent.resolve()
TEST_RESOURCES_DIR = TEST_DIR / 'test_resources'


def test_construct():
    saved_dict = []

    def saver(resource_module, path, source_hash, generator_hash):
        saved_dict.append(resource_module.as_dict)

    generator_ref = mosaic.put(
        resource_registry['command_line.rc', 'compile_resources'])
    compile_resources(
        generator_ref,
        subdir_list=['common', 'resource', 'rc'],
        root_dirs=[TEST_RESOURCES_DIR],
        module_list=['construct_resources_sample'],
        process_name='construct-resources-test-runner',
        saver=saver,
        )

    assert saved_dict  # Was sample resource constructed and saved?
    actual_yaml = yaml.dump(saved_dict[0], sort_keys=False)
    log.info("Resource module:\n%s", actual_yaml)
    expected_yaml = TEST_RESOURCES_DIR.joinpath('construct_resources_sample.expected.yaml').read_text()
    assert actual_yaml == expected_yaml
