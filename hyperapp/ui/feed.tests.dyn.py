import logging
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import feed as feed_module

log = logging.getLogger(__name__)



@mark.fixture
def item_t():
    return pyobj_creg.actor_to_piece(htypes.feed_tests.sample_item)


@mark.config_template_fixture('feed_factory')
def feed_factory_config(item_t):
    list_feed_type = htypes.feed.list_feed_type(
        item_t=mosaic.put(item_t),
        )
    index_tree_feed_type = htypes.feed.index_tree_feed_type(
        item_t=mosaic.put(item_t),
        )
    return {
        htypes.feed_tests.sample_list_feed: htypes.feed.feed_template(
            feed_type=mosaic.put(list_feed_type),
            ),
        htypes.feed_tests.sample_index_tree_feed: htypes.feed.feed_template(
            feed_type=mosaic.put(index_tree_feed_type),
            ),
        }


def test_list_feed_factory(feed_factory):
    piece = htypes.feed_tests.sample_list_feed()
    feed = feed_factory(piece)
    assert isinstance(feed, feed_module.ListFeed), repr(feed)


def test_index_tree_feed_factory(feed_factory):
    piece = htypes.feed_tests.sample_index_tree_feed()
    feed = feed_factory(piece)
    assert isinstance(feed, feed_module.IndexTreeFeed), repr(feed)


def test_remote_list_feed_factory(
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        rpc_call_factory,
        subprocess_rpc_server_running,
        client_feed_factory,
        ):

    model = htypes.feed_tests.sample_list_feed()

    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)

    subprocess_name = 'test-remote-list-feed-factory-main'
    with subprocess_rpc_server_running(subprocess_name, identity) as process:
        log.info("Started: %r", process)

        remote_model = htypes.model.remote_model(
            model=mosaic.put(model),
            remote_peer=mosaic.put(process.peer.piece),
            )
        ctx = Context(
            identity=identity,
            )

        feed = client_feed_factory(remote_model, ctx)
        assert isinstance(feed, feed_module.ListFeed), repr(feed)


class SampleSubscriber:
    pass


def test_feed_finalizer(feed_map, feed_factory):
    piece = htypes.feed_tests.sample_list_feed()
    feed = feed_factory(piece)
    subscriber = Mock()
    feed.subscribe(subscriber)
    assert piece in feed_map
    del subscriber
    assert piece not in feed_map


def test_list_feed_actor(feed_type_creg, item_t):
    piece = htypes.feed.list_feed_type(mosaic.put(item_t))
    feed_type = feed_type_creg.animate(piece)
    assert feed_type is feed_module.ListFeed, repr(feed_type)


def test_index_tree_feed_actor(feed_type_creg, item_t):
    piece = htypes.feed.index_tree_feed_type(mosaic.put(item_t))
    feed_type = feed_type_creg.animate(piece)
    assert feed_type is feed_module.IndexTreeFeed, repr(feed_type)


def test_value_feed_actor(item_t):
    piece = htypes.feed.value_feed_type(
        value_t=mosaic.put(item_t),
        )
    feed_type = feed_module.value_feed_from_piece(piece)
    assert feed_type is feed_module.ValueFeed, repr(feed_type)
