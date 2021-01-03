import logging
import pytest

from hyperapp.common.htypes import tString, TRecord, bundle_t
from hyperapp.common.ref import make_ref
from hyperapp.common import cdr_coders  # self-registering
from hyperapp.common.test.util import resolve_type

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'error',
        'resource',
        'core',
        'hyper_ref',
        'module',
        'packet',
        'phony_transport',
        'tcp_transport',
        'test',
        ]


@pytest.fixture
def code_module_list():
    return [
        'server.async_stop',
        'common.dict_coders',
        'common.route_resolver',
        'common.visitor',
        'common.ref_collector',
        'common.unbundler',
        'common.tcp_packet',
        ]


@pytest.mark.parametrize('encoding', ['json', 'cdr'])
def test_tcp_packet(services, encoding):

    tcp_packet_module = services.name2module['common.tcp_packet']
    test_packet_t = resolve_type(services, 'test', 'packet')

    test_packet = test_packet_t(message='hello')
    capsule = services.types.make_capsule(test_packet)
    ref = make_ref(capsule)
    bundle = bundle_t((ref,), (capsule,), ())

    packet = tcp_packet_module.encode_tcp_packet(bundle, encoding)
    assert tcp_packet_module.has_full_tcp_packet(packet)
    assert tcp_packet_module.has_full_tcp_packet(packet + b'x')
    assert not tcp_packet_module.has_full_tcp_packet(packet[:len(packet) - 1])
    decoded_bundle, packet_size = tcp_packet_module.decode_tcp_packet(packet + b'xx')
    assert packet_size == len(packet)
    assert decoded_bundle == bundle
