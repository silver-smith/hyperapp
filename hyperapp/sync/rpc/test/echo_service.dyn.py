import logging
import threading
from pathlib import Path

import yaml

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from . import htypes
from .rpc_endpoint import TimeoutWaitingForResponse

log = logging.getLogger(__name__)


class Echo:

    def echo(self, request, message):
        log.info("Echo.echo: %s; request=%s", message, request)
        return f'{message} to you too'

    def raise_unexpected_error(self, request):
        log.info("Echo.make_unexpected_error: request=%s", request)
        raise RuntimeError("Some unexpected error")

    def raise_test_error(self, request):
        log.info("Echo.raise_test_error: request=%s", request)
        raise htypes.echo_service.test_error("Some error")


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        master_service_bundle = packet_coders.decode('cdr', config['master_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(master_service_bundle)
        master_peer_ref, master_servant_ref = master_service_bundle.roots

        definitions = yaml.safe_load(Path(__file__).parent.joinpath('echo_service.resources.yaml').read_text())
        resources = services.resource_registry.load_definitions(definitions)
        echo_servant_ref = resources['echo_servant']

        master_peer = services.peer_registry.invite(master_peer_ref)

        my_identity = services.generate_rsa_identity(fast=True)
        my_peer_ref = services.mosaic.put(my_identity.peer.piece)

        rpc_endpoint = services.rpc_endpoint_factory()
        services.endpoint_registry.register(my_identity, rpc_endpoint)

        rpc_call = services.rpc_call_factory(rpc_endpoint, master_peer, master_servant_ref, my_identity)

        self._thread = threading.Thread(target=self._run, args=[services.mosaic, rpc_call, my_peer_ref, echo_servant_ref])

        services.on_start.append(self.start)
        services.on_stop.append(self.stop)

    def start(self):
        log.info("Start echo_services thread")
        self._thread.start()

    def stop(self):
        log.info("Stop echo_services thread")
        self._thread.join()
        log.info("echo_services thread is stopped")

    def _run(self, mosaic, rpc_call, my_peer_ref, echo_servant_ref):
        log.info("echo_service thread is started")
        try:
            rpc_call(my_peer_ref, echo_servant_ref)
        except TimeoutWaitingForResponse as x:
            log.info("Timed out waiting for 'run' response - this is expected, because master is already shutting down subprocess: %s", x)
        except Exception as x:
            log.exception("echo_service thread is failed")
        log.info("echo_service thread is finished")
