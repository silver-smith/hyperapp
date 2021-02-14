import pytest

from hyperapp.common.htypes import bundle_t
from hyperapp.common import cdr_coders  # self-registering


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'rsa_identity',
        'phony_route',
        ]


@pytest.fixture
def code_module_list():
    return [
        'common.visitor',
        'common.ref_collector',
        'transport.identity',
        'transport.rsa_identity',
        'sync.async_stop',
        'sync.transport.transport',
        ]


class PhonyRoute:

    def __init__(self, piece):
        self.piece = piece


def test_route_ref_collected(services, htypes):
    identity = services.generate_rsa_identity(fast=True)
    peer_ref = services.mosaic.put(identity.peer.piece)

    route_piece = htypes.phony_route.phony_route()
    route = PhonyRoute(route_piece)
    route_ref = services.mosaic.put(route_piece)

    services.route_table.add_route(peer_ref, route)
    ref_collector = services.ref_collector_factory()
    bundle = ref_collector.make_bundle([peer_ref])

    assert route_ref in bundle.aux_roots
