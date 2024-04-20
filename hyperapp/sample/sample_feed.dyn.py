import asyncio
import logging

from . import htypes
from .services import (
    feed_creg,
    )
from .code.list_diff import ListDiff

log = logging.getLogger(__name__)


async def _send_diff(feed):
    log.info("Sending list diff")
    item = htypes.sample_list.item(44, "Sample item #4")
    await feed.send(ListDiff.Append(item))


async def schedule_sample_feed(piece):
    feed = feed_creg.animate(piece)
    asyncio.create_task(_send_diff(feed))
