import logging
from pathlib import Path

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class TestModuleList:

    def __init__(self, web, service, module_selector, file):
        self._web = web
        self._service = service
        self._module_selector = module_selector
        self._file = file
        self._name_to_item = self._load()

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
        storage = htypes.htest_list.storage(
            list(self._name_to_item.values()))
        self._file.save_piece(storage)

    def list(self, request):
        return list(self._name_to_item.values())

    def open(self, request, current_key):
        item = self._name_to_item[current_key]
        return self._web.summon(item.module_ref)

    def select_module(self, request):
        return self._module_selector

    def set_module(self, request, module_name, module_ref):
        log.info("Set module: %r %s", module_name, module_ref)
        self._name_to_item[module_name] = htypes.htest_list.test_module(module_name, module_ref)
        self._save()
        return self._service

    def collect(self, request, current_key):
        log.info("Collect tests: %s", current_key)
        item = self._name_to_item[current_key]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        servant_name = 'htest_list'
        servant_path = services.servant_path().registry_name(servant_name)

        open_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('open').as_data(services.mosaic),
            state_attr_list=['current_key'],
            name='open',
            )
        select_module_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('select_module').as_data(services.mosaic),
            state_attr_list=[],
            name='select_module',
            )
        collect_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('collect').as_data(services.mosaic),
            state_attr_list=['current_key'],
            name='collect',
            )
        service = htypes.service.list_service(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('list').as_data(services.mosaic),
            dir_list=[[mosaic.put(htypes.htest_list.htest_list_d())]],
            command_ref_list=[
                mosaic.put(open_command),
                mosaic.put(select_module_command),
                mosaic.put(collect_command),
                ],
            key_column_id='module_name',
            column_list=item_t_to_column_list(services.types, htypes.htest_list.test_module),
            )

        module_list_service = services.module_list_service_factory(['available'])
        rpc_callback = htypes.rpc_callback.rpc_callback(
            peer_ref=server_peer_ref,
            servant_path=servant_path.get_attr('set_module').as_data(services.mosaic),
            item_attr_list=['module_name', 'module_ref'],
            )
        module_selector = htypes.selector.selector(
            list_ref=mosaic.put(module_list_service),
            callback_ref=mosaic.put(rpc_callback),
            )

        file = services.file_bundle(Path.home() / '.local/share/hyperapp/server/htest_list.json')
        servant = TestModuleList(services.web, service, module_selector, file)
        services.server_rpc_endpoint.register_servant(servant_name, servant)

        services.server_ref_list.add_ref('htest_list', 'Test list', mosaic.put(service))
