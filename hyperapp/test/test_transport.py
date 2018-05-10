from pathlib import Path
import pytest

from hyperapp.common.identity import Identity
from hyperapp.common.packet_coders import packet_coders
from hyperapp.common import dict_coders, cdr_coders  # self-registering
from hyperapp.test.test_services import Services


HYPERAPP_DIR = Path(__file__).parent.parent.resolve()
BUNDLE_ENCODING = 'json'


type_module_list = [
    'error',
    'resource',
    'core',
    'hyper_ref',
    'module',
    'packet',
    'phony_transport',
    'tcp_transport',
    'encrypted_transport',
    'test',
    ]

server_code_module_list = [
    'common.ref',
    'common.ref_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'server.transport.registry',
    'server.request',
    'server.remoting',
    'server.echo_service',
    ]

client_code_module_list = [
    'common.ref',
    'common.ref_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'client.async_ref_resolver',
    'client.piece_registry',
    'client.transport.registry',
    'client.transport.phony',
    'client.remoting_proxy',
    ]


def encode_bundle(services, bundle):
    return packet_coders.encode(BUNDLE_ENCODING, bundle, services.types.hyper_ref.bundle)

def decode_bundle(services, encoded_bundle):
    return packet_coders.decode(BUNDLE_ENCODING, encoded_bundle, services.types.hyper_ref.bundle)

def make_transport_ref(services):
    types = services.types
    phony_transport_address = types.phony_transport.address()
    phony_transport_ref = services.ref_registry.register_object(types.phony_transport.address, phony_transport_address)
    identity = Identity.generate(fast=True)
    encrypted_transport_address = types.encrypted_transport.address(
        public_key_der=identity.public_key.to_der(),
        base_transport_ref=phony_transport_ref)
    encrypted_transport_ref = services.ref_registry.register_object(types.encrypted_transport.address, encrypted_transport_address)
    #return encrypted_transport_ref
    return phony_transport_ref

def make_echo_service_bundle():
    services = Services(type_module_list, server_code_module_list)
    transport_ref = make_transport_ref(services)
    href_types = services.types.hyper_ref
    service_ref = href_types.service_ref(['test', 'echo'], services.ECHO_SERVICE_ID, transport_ref)
    ref_resolver_ref = services.ref_registry.register_object(href_types.service_ref, service_ref)
    ref_collector = services.ref_collector_factory()
    piece_list = ref_collector.collect_piece(ref_resolver_ref)
    echo_service_bundle = href_types.bundle(ref_resolver_ref, piece_list)
    return encode_bundle(services, echo_service_bundle)

async def make_request_bundle(encoded_echo_service_bundle):
    services = Services(type_module_list, client_code_module_list)
    echo_service_bundle = decode_bundle(services, encoded_echo_service_bundle)
    services.ref_registry.register_bundle(echo_service_bundle)
    proxy = await services.proxy_factory.from_ref(echo_service_bundle.ref)
    await proxy.say('hello')
    request_bundle = services.phony_transport_bundle_list.pop()
    return encode_bundle(services, request_bundle)

def process_request_bundle(encoded_request_bundle):
    services = Services(type_module_list, server_code_module_list)
    request_bundle = decode_bundle(services, encoded_request_bundle)
    services.ref_registry.register_bundle(request_bundle)
    services.transport_resolver.resolve(request_bundle.ref)

@pytest.mark.asyncio
async def test_services_should_load():
    encoded_echo_service_bundle = make_echo_service_bundle()
    encoded_request_bundle = await make_request_bundle(encoded_echo_service_bundle)
    process_request_bundle(encoded_request_bundle)
