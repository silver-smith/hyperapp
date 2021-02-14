import pytest

from hyperapp.common.htypes import bundle_t
from hyperapp.common import cdr_coders  # self-registering


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'rsa_identity',
        'transport',
        'phony_route',
        ]


@pytest.fixture
def code_module_list():
    return [
        'common.visitor',
        'common.ref_collector',
        'common.unbundler',
        'transport.identity',
        'transport.rsa_identity',
        'sync.async_stop',
        'sync.transport.transport',
        ]


class PersistableRoute:

    @classmethod
    def from_piece(cls, piece, phony_route_t):
        return cls(phony_route_t, piece.id)

    def __init__(self, phony_route_t, id):
        self._phony_route_t = phony_route_t
        self._id = id

    def __eq__(self, rhs):
        return self._id == rhs._id

    @property
    def piece(self):
        return self._phony_route_t(self._id)


class NonPersistableRoute:

    @property
    def piece(self):
        return None


@pytest.fixture
def phony_route_t(htypes):
    return htypes.phony_route.phony_route


def test_route_ref_collected(services, htypes, phony_route_t):
    identity = services.generate_rsa_identity(fast=True)
    peer_ref = services.mosaic.put(identity.peer.piece)

    persistable_route = PersistableRoute(phony_route_t, 123)
    persistable_route_ref = services.mosaic.put(persistable_route.piece)
    services.route_table.add_route(peer_ref, persistable_route)

    non_persistable_route = NonPersistableRoute()
    services.route_table.add_route(peer_ref, non_persistable_route)

    ref_collector = services.ref_collector_factory()
    bundle = ref_collector.make_bundle([peer_ref])

    route_association = htypes.transport.route_association(peer_ref, persistable_route_ref)
    route_association_ref = services.mosaic.put(route_association)
    assert bundle.aux_roots == [route_association_ref]

    bundled_ref_list = [
        services.mosaic.register_capsule(capsule)
        for capsule in bundle.capsule_list
        ]
    assert persistable_route_ref in bundled_ref_list  # Should also be bundled.


def test_unbundled_route_registered(services, htypes, phony_route_t):
    services.route_registry.register_actor(phony_route_t, PersistableRoute.from_piece, phony_route_t)

    identity = services.generate_rsa_identity(fast=True)
    peer_ref = services.mosaic.put(identity.peer.piece)

    route = PersistableRoute(phony_route_t, 123)
    route_ref = services.mosaic.put(route.piece)

    route_association = htypes.transport.route_association(peer_ref, route_ref)
    route_association_ref = services.mosaic.put(route_association)

    bundle = bundle_t(roots=(peer_ref,), aux_roots=(route_association_ref,), capsule_list=())

    services.unbundler.register_bundle(bundle)

    assert route in services.route_table.peer_route_list(peer_ref)
