import logging
from functools import partial

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class TestListServant:

    def __init__(self, mosaic, htest_list, module_name):
        self._mosaic = mosaic
        self._htest_list = htest_list
        self._module_name = module_name

    def list(self, request):
        log.info("HTest_list.list")
        module = self._htest_list.dict[self._module_name]
        return [
            htypes.htest.test(name) for name
            in module.test_list
            ]

    def run(self, request, current_key):
        log.info("Run test: %s/%s", self._module_name, current_key)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._server_peer_ref = services.mosaic.put(services.server_identity.peer.piece)
        self._servant_name = 'htest_list'
        services.server_rpc_endpoint.register_servant(self._servant_name, partial(
            self._htest_list_servant,
            services.mosaic,
            services.htest_list,
            ))
        services.htest_list_service_factory = partial(
            self.htest_list_service_factory,
            services.mosaic,
            services.types,
            services.servant_path,
            )

    def htest_list_service_factory(self, mosaic, types, servant_path_factory, module_name):
        servant_path = servant_path_factory().registry_name(self._servant_name).parameterized(module_name)
        run_command = htypes.rpc_command.rpc_command(
            peer_ref=self._server_peer_ref,
            servant_path=servant_path.get_attr('run').as_data,
            state_attr_list=['current_key'],
            name='run',
            )
        return htypes.service.list_service(
            peer_ref=self._server_peer_ref,
            servant_path=servant_path.get_attr('list').as_data,
            dir_list=[[mosaic.put(htypes.htest.htest_list_d())]],
            command_ref_list=[
                mosaic.put(run_command),
                ],
            key_attribute='name',
            )

    def _htest_list_servant(
            self,
            mosaic,
            htest_list,
            module_name,
            ):
        return TestListServant(
            mosaic,
            htest_list,
            module_name,
            )
