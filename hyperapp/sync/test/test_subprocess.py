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
        )
    with subprocess:
        pass


def test_import_failure(services):
    subprocess = services.subprocess(
        'subprocess',
        additional_module_dirs=[Path(__file__).parent],
        code_module_list=[
            'import_failure',
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
        additional_module_dirs=[Path(__file__).parent],
        code_module_list=[
            'module_init_failure',
            ],
        )
    with pytest.raises(AssertionError) as excinfo:
        with subprocess:
            time.sleep(sleep_sec)
    assert str(excinfo.value) == 'Test module init failure'
