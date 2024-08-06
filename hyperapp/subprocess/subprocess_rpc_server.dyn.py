import itertools
import logging
import threading
from contextlib import contextmanager

from .services import (
    add_subprocess_server_connection,
    fn_to_ref,
    partial_ref,
    peer_registry,
    rpc_call_factory,
    rpc_submit_factory,
    )
from .code.subprocess_rpc_server_main import rpc_server_main
from .code.rpc_proxy import RpcProxy

log = logging.getLogger(__name__)


class _RpcServerProcess:

    def __init__(self, id, name, connection, peer, rpc_endpoint, identity, timeout_sec):
        self.id = id
        self.name = name
        self.connection = connection
        self.peer = peer
        self._rpc_endpoint = rpc_endpoint
        self._identity = identity
        self._timeout_sec = timeout_sec

    def __repr__(self):
        return f"<RpcServerProcess: {self.name}>"

    def rpc_submit(self, servant_fn):
        servant_fn_ref = fn_to_ref(servant_fn)
        return rpc_submit_factory(
            self._rpc_endpoint, self.peer, servant_fn_ref, self._identity)

    def rpc_call(self, servant_fn):
        servant_fn_ref = fn_to_ref(servant_fn)
        return rpc_call_factory(
            self._rpc_endpoint, self.peer, servant_fn_ref, self._identity, self._timeout_sec)

    def proxy(self, servant_ref):
        return RpcProxy(self._rpc_endpoint, self._identity, self.peer, servant_ref, self._timeout_sec)


_subprocess_id_counter = itertools.count()
_callback_signals = {}  # subprocess_id -> event.
_subprocess_peer = {}  # subprocess_id -> Peer.


def _rpc_subprocess_callback(request, subprocess_name, subprocess_id, subprocess_peer):
    log.info("Rpc subprocess callback from %r #%d %s is called", subprocess_name, subprocess_id, request.sender)
    _subprocess_peer[subprocess_id] = peer_registry.animate(subprocess_peer)
    _callback_signals[subprocess_id].set()


def subprocess_rpc_server_running(subprocess_running):

    @contextmanager
    def _subprocess_rpc_server(name, rpc_endpoint, identity, timeout_sec=10):
        subprocess_id = next(_subprocess_id_counter)
        _callback_signals[subprocess_id] = event = threading.Event()
        main_ref = partial_ref(
            rpc_server_main,
            name=name,
            master_peer_piece=identity.peer.piece,
            master_servant_ref=fn_to_ref(_rpc_subprocess_callback),
            subprocess_id=subprocess_id,
        )
        with subprocess_running(name, main_ref) as process:
            connection_rec = add_subprocess_server_connection(name, process.connection, process.sent_refs)
            try:
                if not event.wait(timeout=timeout_sec):
                    raise RuntimeError(f"Timed out waiting for subprocess #{subprocess_id} {name!r} ({timeout_sec} sec)")
                peer = _subprocess_peer[subprocess_id]
                log.info("Rpc server #%d %r is started with peer %s", subprocess_id, name, peer)
                yield _RpcServerProcess(subprocess_id, name, process.connection, peer, rpc_endpoint, identity, timeout_sec)
            finally:
                connection_rec.close()
    return _subprocess_rpc_server
