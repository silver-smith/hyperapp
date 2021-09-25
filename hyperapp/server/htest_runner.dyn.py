import logging
import threading

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class Runner:

    def __init__(self, import_module):
        self._import_module = import_module

    def collect_tests(self, request, module_name):
        log.info("Collect tests: %s", module_name)
        module = self._import_module(module_name)
        return [name for name in dir(module) if name.startswith('test')]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        master_service_bundle = packet_coders.decode('cdr', config['signal_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(master_service_bundle)
        master_peer_ref, *master_servant_path_refs = master_service_bundle.roots

        master_peer = services.peer_registry.invite(master_peer_ref)
        signal_servant_path = services.servant_path_from_data(master_servant_path_refs)

        my_identity = services.generate_rsa_identity(fast=True)
        my_peer_ref = services.mosaic.put(my_identity.peer.piece)

        rpc_endpoint = services.rpc_endpoint()
        services.endpoint_registry.register(my_identity, rpc_endpoint)

        servant_name = 'htest_runner'
        servant_path = services.servant_path().registry_name(servant_name)

        servant = Runner(services.import_module)
        rpc_endpoint.register_servant(servant_name, servant)

        rpc_call = services.rpc_call(rpc_endpoint, master_peer, signal_servant_path, my_identity, timeout_sec=20)

        self._thread = threading.Thread(target=self._run, args=[services.mosaic, rpc_call, my_peer_ref, servant_path])

        services.on_start.append(self.start)
        services.on_stop.append(self.stop)

    def start(self):
        log.info("Start htest start signal thread")
        self._thread.start()

    def stop(self):
        log.info("Stop htest start signal thread")
        self._thread.join()
        log.info("Htest start signal thread is stopped")

    def _run(self, mosaic, rpc_call, my_peer_ref, servant_path):
        log.info("Htest start signal thread is started")
        try:
            rpc_call(my_peer_ref, servant_path.as_data)
        except Exception as x:
            log.exception("Htest start signal thread is failed")
        log.info("Htest start signal thread is finished")
