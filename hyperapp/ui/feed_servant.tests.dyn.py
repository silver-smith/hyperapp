from . import htypes
from .fixtures import feed_fixtures
from .tested.code import feed_servant


def test_server_feed(generate_rsa_identity, server_feed):
    identity = generate_rsa_identity(fast=True)
    model = htypes.feed_servant_tests.sample_model()
    server_feed.add(identity.peer, model)
