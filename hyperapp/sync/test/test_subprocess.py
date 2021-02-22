import time

import pytest

from hyperapp.common import cdr_coders  # self-registering


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'transport',
        ]


@pytest.fixture
def code_module_list():
    return [
        'common.visitor',
        'common.ref_collector',
        'common.unbundler',
        'transport.identity',
        'sync.work_dir',
        'sync.async_stop',
        'sync.transport.transport',
        'sync.subprocess_connection',
        'sync.subprocess',
        ]


def test_subprocess(services):
    subprocess = services.subprocess(
        'subprocess',
        type_module_list=[
            'transport',
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
            'common.unbundler',
            'transport.identity',
            'sync.async_stop',
            'sync.transport.transport',
            'sync.subprocess_connection',
            'sync.subprocess_child',
            ],
        )
    with subprocess:
        pass


def test_import_failure(services):
    subprocess = services.subprocess(
        'subprocess',
        type_module_list=[
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
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
        type_module_list=[
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
            'sync.test.module_init_failure',
            ],
        )
    with pytest.raises(AssertionError) as excinfo:
        with subprocess:
            time.sleep(sleep_sec)
    assert str(excinfo.value) == 'Test module init failure'
