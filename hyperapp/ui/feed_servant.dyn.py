import logging
from collections import defaultdict

from .code.mark import mark

log = logging.getLogger(__name__)



class RemoteSubscription:

    def __init__(self, remote_peer):
        self._remote_peer = remote_peer

    def process_diff(self, diff):
        log.info("Sending diff %s to %s", diff, self._remote_peer)


class ServerFeed:

    def __init__(self, feed_factory):
        self._feed_factory = feed_factory
        self._peer_to_models = defaultdict(set)
        self._subscriptions = {}  # (remote_peer, model) -> RemoteSubscription

    def add(self, remote_peer, model):
        self._peer_to_models[remote_peer].add(model)
        feed = self._feed_factory(model)
        subscription = RemoteSubscription(remote_peer)
        feed.subscribe(subscription)
        self._subscriptions[remote_peer, model] = subscription


@mark.service
def server_feed(feed_factory):
    return ServerFeed(feed_factory)


def subscribe_server_feed(feed_factory, server_feed, request, real_model):
    log.info("%s is subscribing feed: %s", request.remote_peer, real_model)
    server_feed.add(request.remote_peer, real_model)
