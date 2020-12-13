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
        type_module_list=[],
        code_module_list=[],
        )
    with subprocess:
        pass
