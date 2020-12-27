import pytest

from hyperapp.common import cdr_coders  # self-registering


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        ]


@pytest.fixture
def code_module_list():
    return [
        'server.work_dir',
        'server.subprocess',
        ]


def test_subprocess(services):
    subprocess = services.subprocess(
        'test_subprocess',
        type_module_list=[
            'error',
            'hyper_ref',
            'resource',
            'module',
            'packet',
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
            ],
        )
    with subprocess:
        pass


def test_import_failure(services):
    subprocess = services.subprocess(
        'import_failure',
        type_module_list=[
            'error',
            'hyper_ref',
            'resource',
            'module',
            'packet',
            ],
        code_module_list=[
            'common.visitor',
            'common.ref_collector',
            'test.import_failure',
            ],
        )
    with pytest.raises(AssertionError) as excinfo:
        with subprocess:
            pass
    assert str(excinfo.value) == 'Test import failure'
