import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class TestModuleListServant:

    def __init__(
            self,
            mosaic,
            web,
            peer_registry,
            rpc_call_factory,
            identity,
            rpc_endpoint,
            # module_selector,
            htest,
            htest_list,
            # htest_list_service_factory,
            # htest_global_list_service_factory,
            # service,
            ):
        self._web = web
        self._mosaic = mosaic
        self._peer_registry = peer_registry
        self._rpc_call_factory = rpc_call_factory
        self._identity = identity
        self._rpc_endpoint = rpc_endpoint
        # self._module_selector = module_selector
        self._htest = htest
        self._htest_list = htest_list
        # self._htest_list_service_factory = htest_list_service_factory
        # self._htest_global_list_service_factory = htest_global_list_service_factory
        # self._service = service
        self._rpc_call = None

    @property
    def _dict(self):
        return self._htest_list.dict

    def list(self, request, peer_ref, servant_ref):
        peer = self._peer_registry.invite(peer_ref)
        log.info("HTest_module_list.list(%s, %s)", peer, servant_ref)
        self._rpc_call = self._rpc_call_factory(self._rpc_endpoint, peer, servant_ref, self._identity)
        return list(self._dict.values())

    def open(self, request, current_key):
        return self._htest_list_service_factory(module_name=current_key)

    def globals(self, request, current_key):
        return self._htest_global_list_service_factory(module_name=current_key)

    def module(self, request, current_key):
        item = self._dict[current_key]
        return self._web.summon(item.module_ref)

    def remove(self, request, current_key):
        self._htest_list.remove(module_name=current_key)
        diff = htypes.service.list_diff(remove_key_list=[self._mosaic.put(current_key)], item_list=[])
        log.info("Send diffs: %s", diff)
        self._rpc_call(diff)

    def set_module(self, request, module_name, module_ref):
        self._htest_list.add(module_name, module_ref)
        return self._service

    def collect_tests(self, request, current_key):
        log.info("Collect tests for module: %r", current_key)
        test_list = self._htest.collect_tests(module_name=current_key)
        new_item = self._htest_list.set_test_list(current_key, test_list)
        diff = htypes.service.list_diff(
            remove_key_list=[self._mosaic.put(current_key)],
            item_list=[self._mosaic.put(new_item)],
            )
        log.info("Send diffs: %s", diff)
        self._rpc_call(diff)

    def collect_globals(self, request, current_key):
        log.info("Collect globals for module: %r", current_key)
        global_list = self._htest.collect_globals(module_name=current_key)
        new_item = self._htest_list.set_global_list(current_key, global_list)
        diff = htypes.service.list_diff(
            remove_key_list=[self._mosaic.put(current_key)],
            item_list=[self._mosaic.put(new_item)],
            )
        log.info("Send diffs: %s", diff)
        self._rpc_call(diff)


def select_module(request, module_selector):
    return module_selector


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_ref_list_piece = services.resource_module_registry['server.server_ref_list']['server_ref_list']
        server_ref_list = services.python_object_creg.animate(server_ref_list_piece)

        service_piece = services.resource_module_registry['server.htest_module_list']['service']
        service = services.python_object_creg.animate(service_piece)
        server_ref_list.add_ref('htest_module_list', 'Test module list', mosaic.put(service))

        # server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        # servant_name = 'htest_module_list'
        # servant_path = services.servant_path().registry_name(servant_name)

        # open_command = htypes.rpc_command.rpc_command(
        #     peer_ref=server_peer_ref,
        #     servant_path=servant_path.get_attr('open').as_data,
        #     state_attr_list=['current_key'],
        #     name='open',
        #     )
        # globals_command = htypes.rpc_command.rpc_command(
        #     peer_ref=server_peer_ref,
        #     servant_path=servant_path.get_attr('globals').as_data,
        #     state_attr_list=['current_key'],
        #     name='globals',
        #     )
        # module_command = htypes.rpc_command.rpc_command(
        #     peer_ref=server_peer_ref,
        #     servant_path=servant_path.get_attr('module').as_data,
        #     state_attr_list=['current_key'],
        #     name='module',
        #     )
        # remove_command = htypes.rpc_command.rpc_command(
        #     peer_ref=server_peer_ref,
        #     servant_path=servant_path.get_attr('remove').as_data,
        #     state_attr_list=['current_key'],
        #     name='remove',
        #     )
        # select_module_command = htypes.rpc_command.rpc_command(
        #     peer_ref=server_peer_ref,
        #     servant_path=servant_path.get_attr('select_module').as_data,
        #     state_attr_list=[],
        #     name='select_module',
        #     )
        # collect_tests_command = htypes.rpc_command.rpc_command(
        #     peer_ref=server_peer_ref,
        #     servant_path=servant_path.get_attr('collect_tests').as_data,
        #     state_attr_list=['current_key'],
        #     name='collect_tests',
        #     )
        # collect_globals_command = htypes.rpc_command.rpc_command(
        #     peer_ref=server_peer_ref,
        #     servant_path=servant_path.get_attr('collect_globals').as_data,
        #     state_attr_list=['current_key'],
        #     name='collect_globals',
        #     )
        # service = htypes.service.live_list_service(
        #     peer_ref=server_peer_ref,
        #     servant_path=servant_path.get_attr('list').as_data,
        #     dir_list=[[mosaic.put(htypes.htest.htest_module_list_d())]],
        #     command_ref_list=[
        #         mosaic.put(open_command),
        #         mosaic.put(globals_command),
        #         mosaic.put(module_command),
        #         mosaic.put(remove_command),
        #         mosaic.put(select_module_command),
        #         mosaic.put(collect_tests_command),
        #         mosaic.put(collect_globals_command),
        #         ],
        #     key_attribute='module_name',
        #     )

        # module_list_service = services.module_list_service_factory(['available'])
        # rpc_callback = htypes.rpc_callback.rpc_callback(
        #     peer_ref=server_peer_ref,
        #     servant_path=servant_path.get_attr('set_module').as_data,
        #     item_attr_list=['module_name', 'module_ref'],
        #     )
        # module_selector = htypes.selector.selector(
        #     list_ref=mosaic.put(module_list_service),
        #     callback_ref=mosaic.put(rpc_callback),
        #     )

        # servant = TestModuleListServant(
        #     services.mosaic,
        #     services.web,
        #     services.peer_registry,
        #     services.rpc_call_factory,
        #     services.server_identity,
        #     services.server_rpc_endpoint,
        #     module_selector,
        #     services.htest,
        #     services.htest_list,
        #     services.htest_list_service_factory,
        #     services.htest_global_list_service_factory,
        #     service,
        #     )
        # services.server_rpc_endpoint.register_servant(servant_name, servant)

        # services.server_ref_list.add_ref('htest_module_list', 'Test module list', mosaic.put(service))
