import logging
from collections import defaultdict

from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.remote_feed_receiver import remote_feed_receiver

log = logging.getLogger(__name__)



class RemoteSubscription:

    def __init__(self, rpc_system_call_factory, server_identity, remote_peer, model):
        self._rpc_system_call_factory = rpc_system_call_factory
        self._server_identity = server_identity
        self._remote_peer = remote_peer
        self._model = model

    def process_diff(self, diff):
        log.info("Sending diff %s to %s", diff, self._remote_peer)
        fn = ContextFn(
            rpc_system_call_factory=self._rpc_system_call_factory,
            ctx_params=('model', 'diff'),
            service_params=('diff_creg', 'feed_factory'),
            raw_fn=remote_feed_receiver,
            )
        rpc_call = self._rpc_system_call_factory(
            receiver_peer=self._remote_peer,
            sender_identity=self._server_identity,
            fn=fn,
            )
        ctx = Context()
        call_kw = fn.call_kw(ctx, model=self._model, diff=diff.piece)
        rpc_call(**call_kw)


class ServerFeed:

    def __init__(self, rpc_system_call_factory, feed_factory):
        self._rpc_system_call_factory = rpc_system_call_factory
        self._feed_factory = feed_factory
        self._peer_to_models = defaultdict(set)
        self._subscriptions = {}  # (remote_peer, model) -> RemoteSubscription

    def add(self, server_identity, remote_peer, model):
        self._peer_to_models[remote_peer].add(model)
        feed = self._feed_factory(model)
        subscription = RemoteSubscription(self._rpc_system_call_factory, server_identity, remote_peer, model)
        feed.subscribe(subscription)
        self._subscriptions[remote_peer, model] = subscription


@mark.service
def server_feed(rpc_system_call_factory, feed_factory):
    return ServerFeed(rpc_system_call_factory, feed_factory)


def subscribe_server_feed(feed_factory, server_feed, request, real_model):
    log.info("%s is subscribing feed: %s to %s", request.receiver_identity, real_model, request.remote_peer)
    server_feed.add(request.receiver_identity, request.remote_peer, real_model)
