import logging

import pytest

from hyperapp.common import cdr_coders  # self-registering


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'rsa_identity',
        ]


@pytest.fixture
def code_module_list():
    return [
        'common.visitor',
        'common.ref_collector',
        'common.unbundler',
        'transport.identity',
        'transport.rsa_identity',
        'sync.work_dir',
        'sync.async_stop',
        'sync.transport.transport',
        'sync.transport.endpoint',
        'sync.transport.tcp',
        ]


def test_tcp_tranrport(services):
    pass
