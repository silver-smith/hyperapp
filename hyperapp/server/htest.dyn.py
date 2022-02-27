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

    def __init__(self, rpc_call_factory, rpc_endpoint, identity, peer):
        self._rpc_call_factory = rpc_call_factory
        self._rpc_endpoint = rpc_endpoint
        self._identity = identity
        self._peer = peer

    def rpc_call(self, servant_fn_ref):
        return self._rpc_call_factory(
            self._rpc_endpoint, self._peer, servant_fn_ref, self._identity)


class HTest:

    def __init__(
            self,
            mosaic,
            local_modules,
            resource_module_registry,
            bundler,
            subprocess_factory,
            peer_registry,
            rpc_call_factory,
            identity,
            rpc_endpoint,
            runner_signal_queue,
            runner_is_ready_fn_ref,
            runner_method_collect_attributes_ref,
            ):
        self._mosaic = mosaic
        self._local_modules = local_modules
        self._resource_module_registry = resource_module_registry
        self._bundler = bundler
        self._subprocess_factory = subprocess_factory
        self._peer_registry = peer_registry
        self._rpc_call_factory = rpc_call_factory
        self._identity = identity
        self._rpc_endpoint = rpc_endpoint
        self._runner_signal_queue = runner_signal_queue
        self._runner_is_ready_fn_ref = runner_is_ready_fn_ref
        self._runner_method_collect_attributes_ref = runner_method_collect_attributes_ref

    @contextmanager
    def _subprocess_running(self):
        server_peer_ref = self._mosaic.put(self._identity.peer.piece)
        server_peer_ref_cdr_list = [packet_coders.encode('cdr', server_peer_ref)]

        signal_service_bundle = self._bundler([server_peer_ref, self._runner_is_ready_fn_ref]).bundle
        signal_service_bundle_cdr = packet_coders.encode('cdr', signal_service_bundle)

        subprocess = self._subprocess_factory(
            process_name='htest',
            code_module_list=[
                'resource.legacy_module',
                'resource.legacy_service',
                'resource.attribute',
                'resource.partial',
                'resource.call',
                'sync.transport.tcp',  # Unbundler wants tcp route.
                'server.subprocess_report_home',
                ],
            config = {
                'server.subprocess_report_home': {'signal_service_bundle_cdr': signal_service_bundle_cdr},
                'sync.subprocess_child': {'master_peer_ref_cdr_list': server_peer_ref_cdr_list},
                },
            )
        with subprocess:
            log.info("Waiting for runner signal.")
            runner_peer_ref = self._runner_signal_queue.get(timeout=20)
            runner_peer = self._peer_registry.invite(runner_peer_ref)
            log.info("Got runner signal: peer=%s", runner_peer)

            yield RunnerProcess(self._rpc_call_factory, self._rpc_endpoint, self._identity, runner_peer)

    def collect_globals(self, module_name):
        log.info("Collect globals from: %s", module_name)
        with self._subprocess_running() as process:
            call = process.rpc_call(self._runner_method_collect_attributes_ref)
            module = self._local_modules.by_name[module_name]
            module_ref = self._mosaic.put(module)
            global_list = call(module_ref)
            log.info("Collected global list: %s", global_list)
            return global_list

    def construct_resources(self, module_name):
        log.info("Construct resources from: %s", module_name)
        name_to_module = {
            var_name: resource_module_name
            for resource_module_name, resource_module in self._resource_module_registry.items()
            for var_name in resource_module
            }
        import_set = {}
        with self._subprocess_running() as process:
            call = process.rpc_call(self._runner_method_collect_attributes_ref)
            module = self._local_modules.by_name[module_name]
            module_ref = self._mosaic.put(module)
            global_list = call(module_ref)
            log.info("Global list: %s", global_list)
            for fn in global_list:
                self._process_fn(module_name, module_ref, name_to_module, import_set, fn)

    def _process_fn(self, module_name, module_ref, name_to_module, import_set, fn):
        for param_name in fn.param_list:
            resource_module_name = name_to_module[param_name]
            import_set.add(resource_module_name)


def runner_signal_queue():
    return queue.Queue()


def runner_is_ready(request, runner_peer_ref, queue):
    queue.put(runner_peer_ref)


def htest_list_file(file_bundle):
    return file_bundle(Path.home() / '.local/share/hyperapp/server/htest_list.json')
