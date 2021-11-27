import logging
from functools import partial

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class GlobalListServant:

    def __init__(self, builtin_services, mosaic, local_modules, htest, htest_list, module_name):
        self._builtin_services = builtin_services
        self._mosaic = mosaic
        self._local_modules = local_modules
        self._htest = htest
        self._htest_list = htest_list
        self._module_name = module_name

    def list(self, request):
        log.info("HTest_global_list.list")
        module = self._htest_list.dict[self._module_name]
        return module.global_list

    def run(self, request, current_key):
        global_name = current_key
        module = self._htest_list.dict[self._module_name]
        [global_fn] = [gl for gl in module.global_list if gl.name == global_name]
        param_service_list = []
        additional_module_list = []
        for param_name in global_fn.param_list:
            param_service_list.append(param_name)
            if param_name in self._builtin_services:
                continue
            provider_module_list = self._local_modules.by_requirement[param_name]
            if len(provider_module_list) != 1:
                raise RuntimeError(f"{param_name!r} provided by {len(provider_module_list)}, but expected exactly one ({provider_module_list})")
            additional_module_list.append(list(provider_module_list)[0])
        self._htest.run_global(self._module_name, global_name, param_service_list, additional_module_list)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._server_peer_ref = services.mosaic.put(services.server_identity.peer.piece)
        self._servant_name = 'htest_global_list'
        services.server_rpc_endpoint.register_servant(self._servant_name, partial(
            self._htest_global_list_servant,
            services.builtin_services,
            services.mosaic,
            services.local_modules,
            services.htest,
            services.htest_list,
            ))
        services.htest_global_list_service_factory = partial(
            self.htest_global_list_service_factory,
            services.mosaic,
            services.types,
            services.servant_path,
            )

    def htest_global_list_service_factory(self, mosaic, types, servant_path_factory, module_name):
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
            dir_list=[[mosaic.put(htypes.htest.htest_global_list_d())]],
            command_ref_list=[
                mosaic.put(run_command),
                ],
            key_attribute='name',
            )

    def _htest_global_list_servant(
            self,
            builtin_services,
            mosaic,
            local_modules,
            htest,
            htest_list,
            module_name,
            ):
        return GlobalListServant(
            builtin_services,
            mosaic,
            local_modules,
            htest,
            htest_list,
            module_name,
            )
