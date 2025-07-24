import logging

from .code.mark import mark

log = logging.getLogger(__name__)


@mark.service
def remote_feed_receiver(diff_creg, feed_factory, model, diff):
    diff_obj = diff_creg.animate(diff)
    log.info("Received remote diff for %s: %s", model, diff_obj)
    feed = feed_factory(model)
    feed.send(diff_obj)
