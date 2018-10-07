import logging
import pytest

from hyperapp.common.htypes import bundle_t
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
    'common.ref_resolver',
    'common.route_resolver',
    'common.ref_collector',
    'common.ref_registry_module',
    'common.unbundler',
    'common.tcp_packet',
    ]


@pytest.fixture
def client_services(event_loop):
    return TestClientServices(event_loop, type_module_list, client_code_module_list)


@pytest.mark.parametrize('encoding', ['json', 'cdr'])
def test_tcp_packet(client_services, encoding):

    from hyperapp.common.ref import make_ref, make_capsule
    from hyperapp.common.tcp_packet import has_full_tcp_packet, encode_tcp_packet, decode_tcp_packet

    test_packet_t = client_services.types.test.packet

    test_packet = test_packet_t(message='hello')
    capsule = make_capsule(test_packet)
    ref = make_ref(capsule)
    bundle = bundle_t([ref], [capsule], [])

    packet = encode_tcp_packet(bundle, encoding)
    assert has_full_tcp_packet(packet)
    assert has_full_tcp_packet(packet + b'x')
    assert not has_full_tcp_packet(packet[:len(packet) - 1])
    decoded_bundle, packet_size = decode_tcp_packet(packet + b'xx')
    assert packet_size == len(packet)
    assert decoded_bundle == bundle
