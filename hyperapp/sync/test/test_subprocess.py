import time
from pathlib import Path

import pytest

from hyperapp.common import cdr_coders  # self-registering


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def code_module_list():
    return [
        'sync.subprocess',
        ]


def test_subprocess(services):
    subprocess = services.subprocess(
        'subprocess',
        services.module_dir_list,
        )
    with subprocess:
        pass


def test_import_failure(services):
    subprocess = services.subprocess(
        'subprocess',
        module_dir_list=[*services.module_dir_list, Path(__file__).parent],
        code_module_list=[
            'sync.test.import_failure',
            ],
        )
    with pytest.raises(AssertionError) as excinfo:
        with subprocess:
            pass
    assert str(excinfo.value) == 'Test import failure'


@pytest.mark.parametrize('sleep_sec', [0, 1])
def test_module_init_failure(services, sleep_sec):
    subprocess = services.subprocess(
        'subprocess',
        module_dir_list=[*services.module_dir_list, Path(__file__).parent],
        code_module_list=[
            'sync.test.module_init_failure',
            ],
        )
    with pytest.raises(AssertionError) as excinfo:
        with subprocess:
            time.sleep(sleep_sec)
    assert str(excinfo.value) == 'Test module init failure'
