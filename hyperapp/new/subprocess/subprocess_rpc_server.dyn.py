import itertools
import logging
import threading
from contextlib import contextmanager

from .services import (
    fn_to_ref,
    mark,
    partial_ref,
    subprocess_running_2,
    )
from .code.subprocess_rpc_server_main import rpc_server_main

log = logging.getLogger(__name__)


class _RpcServerProcess:

    def __init__(self, connection):
        self.connection = connection


_subprocess_id_counter = itertools.count()
_callback_signals = {}  # subprocess_id -> event.


def _rpc_subprocess_callback(subprocess_id):
    log.info("Rpc subprocess callback is called")
    _callback_signals[subprocess_id].set()


@mark.service
def subprocess_rpc_server_running():

    @contextmanager
    def _subprocess_rpc_server(name, rpc_endpoint, identity):
        subprocess_id = next(_subprocess_id_counter)
        _callback_signals[subprocess_id] = event = threading.Event()
        main_ref = partial_ref(
            rpc_server_main,
            name=name,
            master_peer_piece=identity.peer.piece,
            master_servant_ref=fn_to_ref(_rpc_subprocess_callback),
            subprocess_id=subprocess_id,
        )
        with subprocess_running_2(name, main_ref) as process:
            if not event.wait(timeout=3):
                raise RuntimeError(f"Timed out waiting for subprocess #{subprocess_id} {name!r} (3 sec)")
            yield _RpcServerProcess(process.connection)
    return _subprocess_rpc_server
