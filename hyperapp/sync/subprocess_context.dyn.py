import logging
from contextlib import contextmanager

from hyperapp.common.htypes.packet_coders import packet_coders

from .services import (
    bundler,
    mosaic,
    hyperapp_dir,
    peer_registry,
    rpc_call_factory,
    runner_is_ready_fn_ref,
    runner_signal_queue,
    subprocess_factory,
    )

_log = logging.getLogger(__name__)


class SubProcess:

    def __init__(self, rpc_endpoint, identity, peer):
        self._rpc_endpoint = rpc_endpoint
        self._identity = identity
        self._peer = peer

    def rpc_call(self, servant_fn_ref):
        return rpc_call_factory(
            self._rpc_endpoint, self._peer, servant_fn_ref, self._identity)


@contextmanager
def subprocess_running(rpc_endpoint, identity, process_name):
    peer_ref = mosaic.put(identity.peer.piece)
    peer_ref_cdr_list = [packet_coders.encode('cdr', peer_ref)]

    signal_service_bundle = bundler([peer_ref, runner_is_ready_fn_ref]).bundle
    signal_service_bundle_cdr = packet_coders.encode('cdr', signal_service_bundle)

    module_dir_list = [
        hyperapp_dir / 'common',
        hyperapp_dir / 'resource',
        hyperapp_dir / 'transport',
        hyperapp_dir / 'sync',
        hyperapp_dir / 'async',
        ]
    code_module_list = [
        'resource.legacy_type',
        'resource.legacy_module',
        'resource.legacy_service',
        'resource.python_module',
        'resource.attribute',
        'resource.partial',
        'resource.call',
        'resource.raw',
        'sync.transport.tcp',  # Unbundler wants tcp route.
        'sync.subprocess_report_home',
        ]
    subprocess = subprocess_factory(
        process_name,
        module_dir_list,
        code_module_list,
        config = {
            'sync.subprocess_report_home': {'signal_service_bundle_cdr': signal_service_bundle_cdr},
            'sync.subprocess_child': {'master_peer_ref_cdr_list': peer_ref_cdr_list},
            },
        )
    with subprocess:
        _log.info("Waiting for runner signal.")
        runner_peer_ref = runner_signal_queue.get(timeout=20)
        runner_peer = peer_registry.invite(runner_peer_ref)
        _log.info("Got runner signal: peer=%s", runner_peer)

        yield SubProcess(rpc_endpoint, identity, runner_peer)
