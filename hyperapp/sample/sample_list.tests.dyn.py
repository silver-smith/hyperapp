import asyncio

from . import htypes
from .fixtures import feed_fixtures
from .tested.code import sample_list


async def test_open_sample_fn_list():
    await sample_list.open_sample_fn_list()


async def test_open_feed_sample_fn_list():
    await sample_list.open_feed_sample_fn_list()


def test_sample_list():
    value = sample_list.sample_list(htypes.sample_list.sample_list())
    assert value


async def test_feed_sample_list(feed_factory):
    piece = htypes.sample_list.feed_sample_list()
    feed = feed_factory(piece)
    value = sample_list.feed_sample_list(piece, feed)
    assert value
    await feed.wait_for_diffs(count=1)


def test_format_model():
    piece = htypes.sample_list.sample_list()
    title = sample_list.format_model(piece)
    assert type(title) is str


def test_format_feed_model():
    piece = htypes.sample_list.feed_sample_list()
    title = sample_list.format_feed_model(piece)
    assert type(title) is str
