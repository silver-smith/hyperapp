import logging
import pytest

from hyperapp.common.htypes import tString, Field, TRecord, bundle_t
from hyperapp.common.ref import make_ref
from hyperapp.test.utils import resolve_type
from hyperapp.test.test_services import TestClientServices

log = logging.getLogger(__name__)


type_module_list = [
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

client_code_module_list = [
    'common.visual_rep_encoders',
    'common.route_resolver',
    'common.visitor',
    'common.ref_collector',
    'common.unbundler',
    'common.tcp_packet',
    ]


@pytest.fixture
def client_services(event_loop):
    return TestClientServices(event_loop, type_module_list, client_code_module_list)


@pytest.mark.parametrize('encoding', ['json', 'cdr'])
def test_tcp_packet(client_services, encoding):

    tcp_packet_module = client_services.name2module['common.tcp_packet']
    test_packet_t = resolve_type(client_services, 'test', 'packet')

    test_packet = test_packet_t(message='hello')
    capsule = client_services.type_resolver.make_capsule(test_packet)
    ref = make_ref(capsule)
    bundle = bundle_t([ref], [capsule], [])

    packet = tcp_packet_module.encode_tcp_packet(bundle, encoding)
    assert tcp_packet_module.has_full_tcp_packet(packet)
    assert tcp_packet_module.has_full_tcp_packet(packet + b'x')
    assert not tcp_packet_module.has_full_tcp_packet(packet[:len(packet) - 1])
    decoded_bundle, packet_size = tcp_packet_module.decode_tcp_packet(packet + b'xx')
    assert packet_size == len(packet)
    assert decoded_bundle == bundle
