import logging
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


def _rpc_subprocess_callback():
    log.info("Rpc subprocess callback is called")


@mark.service
def subprocess_rpc_server_running():

    @contextmanager
    def _subprocess_rpc_server(name, rpc_endpoint, identity):
        main_ref = partial_ref(
            rpc_server_main,
            name=name,
            master_peer_piece=identity.peer.piece,
            servant_ref=fn_to_ref(_rpc_subprocess_callback),
        )
        with subprocess_running_2(name, main_ref) as process:
            yield _RpcServerProcess(process.connection)
    return _subprocess_rpc_server

