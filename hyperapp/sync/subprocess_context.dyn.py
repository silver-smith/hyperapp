import logging
from contextlib import contextmanager

from hyperapp.common.htypes.packet_coders import packet_coders

from .services import (
    bundler,
    mosaic,
    peer_registry,
    rpc_call_factory,
    runner_is_ready_fn_ref,
    runner_signal_queue,
    subprocess_factory,
    )

_log = logging.getLogger(__name__)


class SubProcess:

    def __init__(self, rpc_endpoint, identity, peer):
        self._rpc_endpoint
        self._identity
        self._peer = peer

    def rpc_call(self, servant_fn_ref):
        return rpc_call_factory(
            self._rpc_endpoint, self._peer, servant_fn_ref, self._identity)


@contextmanager
def subprocess_running(rpc_endpoint, identity, process_name):
    server_peer_ref = mosaic.put(identity.peer.piece)
    server_peer_ref_cdr_list = [packet_coders.encode('cdr', server_peer_ref)]

    signal_service_bundle = bundler([server_peer_ref, runner_is_ready_fn_ref]).bundle
    signal_service_bundle_cdr = packet_coders.encode('cdr', signal_service_bundle)

    subprocess = subprocess_factory(
        process_name=process_name,
        code_module_list=[
            'resource.legacy_type',
            'resource.legacy_module',
            'resource.legacy_service',
            'resource.python_module',
            'resource.attribute',
            'resource.partial',
            'resource.call',
            'resource.raw',
            'sync.transport.tcp',  # Unbundler wants tcp route.
            'server.subprocess_report_home',
            ],
        config = {
            'server.subprocess_report_home': {'signal_service_bundle_cdr': signal_service_bundle_cdr},
            'sync.subprocess_child': {'master_peer_ref_cdr_list': server_peer_ref_cdr_list},
            },
        )
    with subprocess:
        _log.info("Waiting for runner signal.")
        runner_peer_ref = runner_signal_queue.get(timeout=20)
        runner_peer = peer_registry.invite(runner_peer_ref)
        _log.info("Got runner signal: peer=%s", runner_peer)

        yield SubProcess(rpc_endpoint, identity, runner_peer)
