import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from . import htypes
from .code.mark import mark
from .code.list_diff import IndexListDiff

log = logging.getLogger(__name__)


@mark.model
def sample_list(piece):
    log.info("Sample list: Called model")
    return [
        htypes.sample_list.item(1, "first", "First sample"),
        htypes.sample_list.item(2, "second", "Second sample"),
        htypes.sample_list.item(3, "third", "Third sample"),
        ]


@mark.global_command
async def open_sample_fn_list():
    return htypes.sample_list.sample_list()


def _send_diff(feed):
    log.info("Sending diff")
    item = htypes.sample_list.item(4, "fourth","Sample item #4")
    feed.send(IndexListDiff.Append(item))


def _send_diff_sync(feed):
    time.sleep(1)
    _send_diff(feed)


@mark.service
def _sample_thread_pool():
    pool = ThreadPoolExecutor(max_workers=1)
    log.info("Sample list: Thread pool created")
    yield pool
    pool.shutdown()


def _post_diff_task(thread_pool, feed):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        log.info("Sending diff sync")
        thread_pool.submit(_send_diff_sync, feed)
    else:
        log.info("Sending diff async")
        loop.call_later(1, _send_diff, feed)


@mark.model
def feed_sample_list(piece, _sample_thread_pool, feed_factory):
    feed = feed_factory(piece)
    _post_diff_task(_sample_thread_pool, feed)
    return [
        htypes.sample_list.item(1, "first", "First sample"),
        htypes.sample_list.item(2, "second", "Second sample"),
        htypes.sample_list.item(3, "third", "Third sample"),
        ]


@mark.global_command
async def open_feed_sample_fn_list():
    return htypes.sample_list.feed_sample_list()


@mark.actor.formatter_creg
def format_model(piece):
    return "Sample list"


@mark.actor.formatter_creg
def format_feed_model(piece):
    return "Sample feed list"
