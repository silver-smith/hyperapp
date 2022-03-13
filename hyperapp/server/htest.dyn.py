import logging
import queue
import re
from contextlib import contextmanager
from functools import cached_property, partial
from pathlib import Path

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


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
            resource_type_reg,
            resource_module_registry,
            resource_module_factory,
            python_object_creg,
            bundler,
            subprocess_factory,
            peer_registry,
            rpc_call_factory,
            identity,
            rpc_endpoint,
            runner_signal_queue,
            runner_is_ready_fn_ref,
            runner_method_collect_attributes_ref,
            runner_method_get_function_result_type_ref,
            ):
        self._mosaic = mosaic
        self._local_modules = local_modules
        self._resource_type_reg = resource_type_reg
        self._resource_module_registry = resource_module_registry
        self._resource_module_factory = resource_module_factory
        self._python_object_creg = python_object_creg
        self._bundler = bundler
        self._subprocess_factory = subprocess_factory
        self._peer_registry = peer_registry
        self._rpc_call_factory = rpc_call_factory
        self._identity = identity
        self._rpc_endpoint = rpc_endpoint
        self._runner_signal_queue = runner_signal_queue
        self._runner_is_ready_fn_ref = runner_is_ready_fn_ref
        self._runner_method_collect_attributes_ref = runner_method_collect_attributes_ref
        self._runner_method_get_function_result_type_ref = runner_method_get_function_result_type_ref

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

    def construct_resources(self, module_name, root_dir):
        log.info("Construct resources from: %s", module_name)
        name_to_module = {
            var_name: resource_module_name
            for resource_module_name, resource_module in self._resource_module_registry.items()
            for var_name in resource_module
            }
        module_rpath = module_name.replace('.', '/')
        resource_module = self._resource_module_factory(
            module_name, root_dir / f'{module_rpath}.resources.yaml', allow_missing=True)
        module_res_name = f'legacy_module.{module_name}'
        resource_module.add_import(module_res_name)
        with self._subprocess_running() as process:
            collect_attributes_call = process.rpc_call(self._runner_method_collect_attributes_ref)
            module = self._local_modules.by_name[module_name]
            module_ref = self._mosaic.put(module)
            global_list = collect_attributes_call(module_ref)
            log.info("Global list: %s", global_list)
            for globl in global_list:
                self._process_fn(module_name, resource_module, process, collect_attributes_call, module_res_name, name_to_module, globl)
        return resource_module

    def _process_fn(self, module_name, resource_module, process, collect_attributes_call, module_res_name, name_to_module, globl):
        global_snake_name = camel_to_snake(globl.name)
        attr_res_t = self._resource_type_reg['attribute']
        attr_def = attr_res_t.definition_t(
            object=module_res_name,
            attr_name=globl.name,
            )
        attr_res_name = f'{global_snake_name}_attribute'

        param_to_resource = {}
        for param_name in globl.param_list:
            resource_module_name = name_to_module[param_name]
            resource_name = f'{resource_module_name}.{param_name}'
            param_to_resource[param_name] = resource_name
            resource_module.add_import(resource_name)
        partial_res_t = self._resource_type_reg['partial']
        partial_def_t = partial_res_t.definition_t
        partial_param_def_t = partial_def_t.fields['params'].element_t
        partial_def = partial_def_t(
            function=attr_res_name,
            params=[
                partial_param_def_t(param_name, resource_name)
                for param_name, resource_name
                in param_to_resource.items()
                ],
            )
        partial_res_name = f'{global_snake_name}_partial'

        call_res_t = self._resource_type_reg['call']
        call_def = call_res_t.definition_t(
            function=partial_res_name,
            )
        call_res_name = global_snake_name

        resource_module.set_definition(attr_res_name, attr_res_t, attr_def)
        resource_module.set_definition(partial_res_name, partial_res_t, partial_def)
        resource_module.set_definition(call_res_name, call_res_t, call_def)

        object_res = resource_module[call_res_name]
        log.info("Function resource %s: %r", global_snake_name, object_res)
        attr_list = collect_attributes_call(self._mosaic.put(object_res))
        log.info("Attributes for %s: %r", global_snake_name, attr_list)

        for attr in attr_list:
            if attr.param_list in {(), ('request',)}:
                self._process_service(module_name, resource_module, process, global_snake_name, object_res, attr)

    def _process_service(self, module_name, resource_module, process, global_snake_name, object_res, attr):
        attr_res_t = self._resource_type_reg['attribute']
        attr_def = attr_res_t.definition_t(
            object=global_snake_name,
            attr_name=attr.name,
            )
        attr_res_name = f'{global_snake_name}_{attr.name}_method'
        resource_module.set_definition(attr_res_name, attr_res_t, attr_def)
        attr_res = resource_module[attr_res_name]
        attr_res_ref = self._mosaic.put(attr_res)

        get_result_call = process.rpc_call(self._runner_method_get_function_result_type_ref)
        if attr.param_list == ('request',):
            args = [None]
        else:
            args = []
        result_t = get_result_call(attr_res_ref, *args)
        log.info("Attribute %s.%s result type: %r", global_snake_name, attr.name, result_t)

        if isinstance(result_t, htypes.htest.list_t):
            self._process_list_service(module_name, resource_module, process, global_snake_name, attr, attr_res_name, result_t)

    def _process_list_service(self, module_name, resource_module, process, global_snake_name, attr, attr_res_name, result_t):
        for key_attribute in ['id', 'key', 'name']:
            if key_attribute in result_t.attr_name_list:
                break
        else:
            raise RuntimeError(f"Unable to deduce key attribute for {global_snake_name}.{attr.name}: {result_t}")

        module_type_name = module_name.split('.')[-1]
        dir_t_res_name = f'legacy_type.{module_type_name}.{global_snake_name}_d'
        call_res_t = self._resource_type_reg['call']
        dir_def = call_res_t.definition_t(
            function=dir_t_res_name,
            )
        dir_res_name = f'{global_snake_name}_d'
        resource_module.add_import(dir_t_res_name)
        resource_module.set_definition(dir_res_name, call_res_t, dir_def)

        identity_res_name = 'legacy_service.server_identity'
        service_res_t = self._resource_type_reg['list_service']
        service_def = service_res_t.definition_t(
            identity='legacy_service.server_identity',
            function=attr_res_name,
            dir=dir_res_name,
            commands=[],
            key_attribute=key_attribute,
            )
        service_res_name = f'{global_snake_name}_service'
        resource_module.add_import(identity_res_name)
        resource_module.set_definition(service_res_name, service_res_t, service_def)


def runner_signal_queue():
    return queue.Queue()


def runner_is_ready(request, runner_peer_ref, queue):
    queue.put(runner_peer_ref)


def htest_list_file(file_bundle):
    return file_bundle(Path.home() / '.local/share/hyperapp/server/htest_list.json')
