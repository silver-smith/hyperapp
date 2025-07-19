import logging

log = logging.getLogger(__name__)


def subscribe_server_feed(feed_factory, request, real_model):
    log.info("%s is subscribing feed: %s", request.remote_peer, real_model)
