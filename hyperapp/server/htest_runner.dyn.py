import inspect
import logging
import threading

from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class Runner:

    def __init__(self, services, local_modules, module_registry):
        self._services = services
        self._local_modules = local_modules
        self._module_registry = module_registry

    def collect_tests(self, request, module_name):
        log.info("Collect tests: %s", module_name)
        module = self._import_module(module_name)
        return [name for name in dir(module) if name.startswith('test')]

    def collect_globals(self, request, module_name):
        log.info("Collect globals: %s", module_name)
        module = self._import_module(module_name)
        return list(self._iter_callables(module))

    def run_global(self, request, module_name, global_name, param_service_list, additional_module_list):
        log.info("Run global: %s.%s (additional: %s)", module_name, global_name, [m.module_name for m in additional_module_list])
        module = self._import_module(module_name, additional_module_list)
        fn = getattr(module, global_name)
        kw = {
            name: getattr(self._services, name)
            for name in param_service_list
            }
        object = fn(**kw)
        log.info("Run global %s.%s result: %r", module_name, global_name, object)
        return list(self._iter_callables(object))

    def _iter_callables(self, object):
        for name in dir(object):
            if name.startswith('_'):
                continue
            value = getattr(object, name)
            if not callable(value):
                continue
            try:
                signature = inspect.signature(value)
            except ValueError as x:
                if 'no signature found for builtin type' in str(x):
                    continue
                raise
            param_list = list(signature.parameters.keys())
            yield htypes.htest.global_fn(name, param_list)

    def _import_module(self, module_name, additional_module_list=None):
        module = self._local_modules.by_name[module_name]
        module_list = [module, *(additional_module_list or [])]
        self._module_registry.import_module_list(self._services, module_list, self._local_modules.by_requirement, config_dict={})
        return self._module_registry.get_python_module(module)


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

        rpc_endpoint = services.rpc_endpoint_factory()
        services.endpoint_registry.register(my_identity, rpc_endpoint)

        servant_name = 'htest_runner'
        servant_path = services.servant_path().registry_name(servant_name)

        servant = Runner(services, services.local_modules, services.module_registry)
        rpc_endpoint.register_servant(servant_name, servant)

        rpc_call = services.rpc_call_factory(rpc_endpoint, master_peer, signal_servant_path, my_identity, timeout_sec=20)

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
