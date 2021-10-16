import logging
from pathlib import Path

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class TestModuleList:

    def __init__(self, mosaic, web, peer_registry, servant_path_from_data, rpc_call_factory, identity, rpc_endpoint,
                 htest, service, module_selector, file):
        self._web = web
        self._mosaic = mosaic
        self._peer_registry = peer_registry
        self._servant_path_from_data = servant_path_from_data
        self._rpc_call_factory = rpc_call_factory
        self._identity = identity
        self._rpc_endpoint = rpc_endpoint
        self._htest = htest
        self._service = service
        self._module_selector = module_selector
        self._file = file
        self._name_to_item = self._load()
        self._rpc_call = None

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
            list(self._name_to_item.values()))
        self._file.save_piece(storage)

    def list(self, request, peer_ref, servant_path_data):
        peer = self._peer_registry.invite(peer_ref)
        servant_path = self._servant_path_from_data(servant_path_data)
        self._rpc_call = self._rpc_call_factory(self._rpc_endpoint, peer, servant_path, self._identity)
        log.info("HTest_list.list(%s, %s)", peer, servant_path)
        return list(self._name_to_item.values())

    def open(self, request, current_key):
        item = self._name_to_item[current_key]
        return self._web.summon(item.module_ref)

    def remove(self, request, current_key):
        log.info("Remove module %r", current_key)
        del self._name_to_item[current_key]
        self._save()
        diff = htypes.service.list_diff(remove_key_list=[self._mosaic.put(current_key)], item_list=[])
        log.info("Send diffs: %s", diff)
        self._rpc_call(diff)

    def select_module(self, request):
        return self._module_selector

    def set_module(self, request, module_name, module_ref):
        log.info("Set module: %r %s", module_name, module_ref)
        self._name_to_item[module_name] = htypes.htest.test_module(module_name, module_ref, test_list=[])
        self._save()
        return self._service

    def collect(self, request, current_key):
        log.info("Collect tests for module: %r", current_key)
        item = self._name_to_item[current_key]
        test_list = self._htest.collect_tests(item.module_name)
        item = htypes.htest.test_module(item.module_name, item.module_ref, test_list)
        self._name_to_item[current_key] = item
        diff = htypes.service.list_diff(
            remove_key_list=[self._mosaic.put(current_key)],
            item_list=[self._mosaic.put(item)],
            )
        log.info("Send diffs: %s", diff)
        self._rpc_call(diff)
        self._save()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        servant_name = 'htest_module_list'
        servant_path = services.servant_path().registry_name(servant_name)

        open_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('open').as_data,
            state_attr_list=['current_key'],
            name='open',
            )
        remove_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('remove').as_data,
            state_attr_list=['current_key'],
            name='remove',
            )
        select_module_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('select_module').as_data,
            state_attr_list=[],
            name='select_module',
            )
        collect_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('collect').as_data,
            state_attr_list=['current_key'],
            name='collect',
            )
        service = htypes.service.live_list_service(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('list').as_data,
            dir_list=[[mosaic.put(htypes.htest.htest_list_d())]],
            command_ref_list=[
                mosaic.put(open_command),
                mosaic.put(remove_command),
                mosaic.put(select_module_command),
                mosaic.put(collect_command),
                ],
            key_column_id='module_name',
            column_list=item_t_to_column_list(services.types, htypes.htest.test_module),
            )

        module_list_service = services.module_list_service_factory(['available'])
        rpc_callback = htypes.rpc_callback.rpc_callback(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('set_module').as_data,
            item_attr_list=['module_name', 'module_ref'],
            )
        module_selector = htypes.selector.selector(
            list_ref=mosaic.put(module_list_service),
            callback_ref=mosaic.put(rpc_callback),
            )

        file = services.file_bundle(Path.home() / '.local/share/hyperapp/server/htest_list.json')
        servant = TestModuleList(
            services.mosaic,
            services.web,
            services.peer_registry,
            services.servant_path_from_data,
            services.rpc_call,
            services.server_identity,
            services.server_rpc_endpoint,
            services.htest,
            service,
            module_selector,
            file,
            )
        services.server_rpc_endpoint.register_servant(servant_name, servant)

        services.server_ref_list.add_ref('htest_module_list', 'Test module list', mosaic.put(service))
