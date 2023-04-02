import logging
from contextlib import contextmanager

from .services import (
    mark,
    partial_ref,
    subprocess_running_2,
    )

log = logging.getLogger(__name__)


class _RpcServerProcess:

    def __init__(self, connection):
        self.connection = connection


def _rpc_server_main(connection):
    my_name = "Subprocess rpc server"
    log.info("%s: Started", my_name)


@mark.service
def subprocess_rpc_server():
    main_ref = partial_ref(_rpc_server_main)
    def _subprocess_rpc_server(name, rpc_endpoint, identity):
        with subprocess_running_2(name, main_ref) as process:
            yield _RpcServerProcess(process.connection)
    return subprocess_rpc_server
