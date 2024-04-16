import inspect

import asyncio
import logging
from functools import partial

from . import htypes
from .services import (
    feed_creg,
    )
from .code.list_diff import ListDiff

log = logging.getLogger(__name__)



def _send_diff(feed):
    log.info("Sending list diff")
    item = htypes.sample_list.item(44, "Sample item #4")
    feed.send(ListDiff.Append(item))


async def schedule_sample_feed(piece):
    feed = feed_creg.animate(piece)
    loop = asyncio.get_running_loop()
    loop.call_soon(partial(_send_diff, feed))
