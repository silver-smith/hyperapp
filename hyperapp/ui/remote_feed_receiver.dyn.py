import logging

from . import htypes
from .code.mark import mark
from .services import (
    mosaic,
    )

log = logging.getLogger(__name__)


@mark.service
def remote_feed_receiver(diff_creg, feed_factory, request, model, diff):
    diff_obj = diff_creg.animate(diff)
    log.info("Received remote diff from %s for %s: %s", request.remote_peer, model, diff_obj)
    remote_model = htypes.model.remote_model(
        model=mosaic.put(model),
        remote_peer=mosaic.put(request.remote_peer.piece),
        )
    feed = feed_factory(remote_model)
    feed.send(diff_obj)
