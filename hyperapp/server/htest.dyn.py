import logging
import queue
from contextlib import contextmanager
from functools import cached_property, partial
from pathlib import Path

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class HTestList:

    def __init__(self, file):
        self._file = file
        self._name_to_module = None  # module_name -> htest.test_module

    @cached_property
    def dict(self):
        if self._name_to_module is None:
            self._name_to_module = self._load()
        return self._name_to_module

    def add(self, module_name, module_ref):
        log.info("Add module: %r %s", module_name, module_ref)
        self.dict[module_name] = htypes.htest.test_module(module_name, module_ref, test_list=[], global_list=[])
        self._save()

    def remove(self, module_name):
        log.info("Remove module %r", module_name)
        del self.dict[module_name]
        self._save()

    def set_test_list(self, module_name, test_list):
        old_item = self.dict[module_name]
        new_item = htypes.htest.test_module(module_name, old_item.module_ref, test_list, old_item.global_list)
        self.dict[module_name] = new_item
        self._save()
        return new_item

    def set_global_list(self, module_name, global_list):
        old_item = self.dict[module_name]
        new_item = htypes.htest.test_module(module_name, old_item.module_ref, old_item.test_list, global_list)
        self.dict[module_name] = new_item
        self._save()
        return new_item

    def _load(self):
        try:
            storage = self._file.load_piece()
        except FileNotFoundError:
            return {}
        else:
            return {
                item.module_name: item
                for item in storage.test_module_list
                }

    def _save(self):
        storage = htypes.htest.storage(
            list(self._name_to_module.values()))
        self._file.save_piece(storage)


class RunnerProcess:

    def __init__(self, rpc_call_factory, rpc_endpoint, identity, peer, servant_path):
        self._rpc_call_factory = rpc_call_factory
        self._rpc_endpoint = rpc_endpoint
        self._identity = identity
        self._peer = peer
        self._servant_path = servant_path

    def rpc_call(self, fn_name):
        return self._rpc_call_factory(
            self._rpc_endpoint, self._peer, self._servant_path.get_attr(fn_name), self._identity)


class HTest:

    def __init__(self, mosaic, ref_collector, subprocess_factory, peer_registry,
                 servant_path_factory, servant_path_from_data, rpc_call_factory, identity, rpc_endpoint):
        self._mosaic = mosaic
        self._ref_collector = ref_collector
        self._subprocess_factory = subprocess_factory
        self._peer_registry = peer_registry
        self._servant_path_factory = servant_path_factory
        self._servant_path_from_data = servant_path_from_data
        self._rpc_call_factory = rpc_call_factory
        self._identity = identity
        self._rpc_endpoint = rpc_endpoint

    def collect_tests(self, module_name):
        log.info("Collect tests from: %s", module_name)
        with self._subprocess_running() as process:
            collect_call = process.rpc_call('collect_tests')
            test_list = collect_call(module_name)
            log.info("Collected test list: %s", test_list)
            return test_list

    def collect_globals(self, module_name):
        log.info("Collect global from: %s", module_name)
        with self._subprocess_running() as process:
            collect_call = process.rpc_call('collect_globals')
            global_list = collect_call(module_name)
            log.info("Collected global list: %s", global_list)
            return global_list

    @contextmanager
    def _subprocess_running(self):
        server_peer_ref = self._mosaic.put(self._identity.peer.piece)
        server_peer_ref_cdr_list = [packet_coders.encode('cdr', server_peer_ref)]

        runner_signal_queue = queue.Queue()
        signal_servant_name = 'htest_runner_started_signal'
        signal_servant = partial(self._runner_is_ready, runner_signal_queue)
        self._rpc_endpoint.register_servant(signal_servant_name, signal_servant)
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
            runner_peer_ref, runner_servant_path_refs = runner_signal_queue.get(timeout=20)
            runner_peer = self._peer_registry.invite(runner_peer_ref)
            runner_servant_path = self._servant_path_from_data(runner_servant_path_refs)
            log.info("Got runner signal: peer=%s servant=%s", runner_peer, runner_servant_path)

            yield RunnerProcess(self._rpc_call_factory, self._rpc_endpoint, self._identity, runner_peer, runner_servant_path)
        
    @staticmethod
    def _runner_is_ready(queue, request, runner_peer_ref, runner_servant_path):
        queue.put((runner_peer_ref, runner_servant_path))


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.htest = HTest(
            services.mosaic,
            services.ref_collector,
            services.subprocess,
            services.peer_registry,
            services.servant_path,
            services.servant_path_from_data,
            services.rpc_call_factory,
            services.server_identity,
            services.server_rpc_endpoint,
            )

        file = services.file_bundle(Path.home() / '.local/share/hyperapp/server/htest_list.json')
        services.htest_list = HTestList(file)
