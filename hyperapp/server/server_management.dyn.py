# server management module: used to expose commands from all modules in one list

import logging
from ..common.interface import core as core_types
from ..common.interface import server_management as server_management_types
from ..common.interface import hyper_ref as href_types
from ..common.interface import ref_list as ref_list_types
from ..common.url import Url
from ..common.local_server_paths import (
    LOCAL_SERVER_REF_LIST_REF_PATH,
    save_bytes_to_file,
    )
from .object import Object, SmallListObject
from .module import Module
from .command import command

log = logging.getLogger(__name__)


MODULE_NAME = 'management'
REF_LIST_RESOLVER_SERVICE_CLASS_NAME = 'ref_list_resolver'


class CommandList(SmallListObject):

    iface = server_management_types.server_management
    impl_id = 'proxy_list'

    @classmethod
    def get_path(cls):
        return this_module.make_path()

    def __init__(self, module_registry):
        SmallListObject.__init__(self, core_types)
        self._module_registry = module_registry

    def fetch_all_elements(self, request):
        return list(map(self.cmd2element, self._module_registry.get_all_modules_commands()))

    def cmd2element(self, cmd):
        commands = [self.command_open]
        id = '%s.%s' % (cmd.module_name, cmd.id)
        return self.Element(self.Row(id, cmd.module_name, cmd.text, cmd.desc), commands)

    @command('open', kind='element')
    def command_open(self, request):
        module_name, command_id = request.params.element_key.split('.')
        module = self._module_registry.get_module_by_name(module_name)
        return module.run_command(request, command_id)


class RefListResolverService(Object):

    iface = ref_list_types.ref_list_resolver
    class_name = REF_LIST_RESOLVER_SERVICE_CLASS_NAME

    @classmethod
    def get_path(cls):
        return this_module.make_path(cls.class_name)

    def __init__(self, management_ref_list):
        Object.__init__(self)
        self._management_ref_list = management_ref_list

    def resolve(self, path):
        path.check_empty()
        return self
    
    @command('get_ref_list')
    def command_get_ref_list(self, request, ref_list_id):
        ref_list = self._management_ref_list.get_ref_list()
        return request.make_response_result(ref_list=ref_list_types.ref_list(ref_list=ref_list))


class ManagementRefList(object):

    def __init__(self):
        self._ref_list = []

    def add_ref(self, id, ref):
        self._ref_list.append(ref_list_types.ref_item(id, ref))

    def get_ref_list(self):
        return self._ref_list


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)
        self._module_registry = services.module_registry
        self._server = services.server
        self._tcp_server = services.tcp_server
        self._ref_storage = services.ref_storage
        services.management_ref_list = self._management_ref_list = ManagementRefList()
        self._ref_list_resolver_service = RefListResolverService(self._management_ref_list)

    def resolve(self, iface, path):
        class_name = path.pop_str_opt()
        if class_name and class_name == RefListResolverService.class_name:
            return self._ref_list_resolver_service.resolve(path)
        path.check_empty()
        return CommandList(self._module_registry)

    def init_phase3(self):
        service_url = Url(RefListResolverService.iface, self._server.get_public_key(), RefListResolverService.get_path())
        service = ref_list_types.ref_list_service(service_url=service_url.to_data())
        service_ref = self._ref_storage.add_object(ref_list_types.ref_list_service, service)
        ref_list = ref_list_types.dynamic_ref_list(
            ref_list_service=service_ref,
            ref_list_id='server-management',
            )
        ref = self._ref_storage.add_object(ref_list_types.dynamic_ref_list, ref_list)
        self._management_ref_list.add_ref('server-ref-list', ref)
        ref_path = save_bytes_to_file(ref, LOCAL_SERVER_REF_LIST_REF_PATH)
        log.info('Server ref list ref is saved to: %s', ref_path)

def get_management_url(public_key):
    return Url(CommandList.iface, public_key, CommandList.get_path())
