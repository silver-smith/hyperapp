import logging
import queue
from functools import partial

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class Htest:

    def __init__(self, mosaic, ref_collector, subprocess_factory, servant_path_factory, server_identity, server_rpc_endpoint):
        self._mosaic = mosaic
        self._ref_collector = ref_collector
        self._subprocess_factory = subprocess_factory
        self._servant_path_factory = servant_path_factory
        self._server_identity = server_identity
        self._server_rpc_endpoint = server_rpc_endpoint

    def collect_tests(self, module_name):
        log.info("Collect tests from: %s", module_name)

        server_peer_ref = self._mosaic.put(self._server_identity.peer.piece)
        server_peer_ref_cdr_list = [packet_coders.encode('cdr', server_peer_ref)]

        runner_signal_queue = queue.Queue()
        signal_servant_name = 'htest_runner_started_signal'
        signal_servant = partial(self._runner_is_ready, runner_signal_queue)
        self._server_rpc_endpoint.register_servant(signal_servant_name, signal_servant)
        signal_servant_path = self._servant_path_factory().registry_name(signal_servant_name)

        signal_service_bundle = self._ref_collector([server_peer_ref, *signal_servant_path.as_data]).bundle
        signal_service_bundle_cdr = packet_coders.encode('cdr', signal_service_bundle)

        subprocess = self._subprocess_factory(
            process_name='htest',
            code_module_list=[
                'sync.transport.tcp',  # Unbundler wants tcp route.
                'server.htest_runner',
                ],
            config = {
                'server.htest_runner': {'signal_service_bundle_cdr': signal_service_bundle_cdr},
                'sync.subprocess_child': {'master_peer_ref_cdr_list': server_peer_ref_cdr_list},
                },
            )
        with subprocess:
            log.info("Waiting for runner signal.")
            runner_peer_ref, runner_servant_path = runner_signal_queue.get(timeout=20)
            log.info("Got runner signal: peer=%s servant=%s", runner_peer_ref, runner_servant_path)

    @staticmethod
    def _runner_is_ready(queue, request, runner_peer_ref, runner_servant_path):
        queue.put((runner_peer_ref, runner_servant_path))


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.htest = Htest(
            services.mosaic,
            services.ref_collector,
            services.subprocess,
            services.servant_path,
            services.server_identity,
            services.server_rpc_endpoint,
            )
