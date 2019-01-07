# server management module: used to expose commands from all modules in one list

import logging
from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module
from hyperapp.server.command import command
from . import htypes
from .local_server_paths import (
    LOCAL_SERVER_DYNAMIC_REF_LIST_REF_PATH,
    save_bundle_to_file,
    )

log = logging.getLogger(__name__)


MODULE_NAME = 'management'
DYNAMIC_REF_LIST_SERVICE_ID = 'dynamic_ref_list'
SERVER_MANAGEMENT_REF_LIST_ID = 'server_management'


class DynamicRefListService(object):

    def __init__(self):
        self._id2ref_list = {}

    def register_ref_list(self, id, ref_list):
        self._id2ref_list[id] = ref_list
    
    def rpc_get_ref_list(self, request, ref_list_id):
        dynamic_ref_list = self._id2ref_list[ref_list_id]
        ref_list = dynamic_ref_list.get_ref_list()
        return request.make_response_result(ref_list=htypes.ref_list.ref_list(ref_list=ref_list))


class ManagementRefList(object):

    def __init__(self):
        self._ref_list = []

    def add_ref(self, id, ref):
        log.info('Adding management ref for %r: %s', id, ref_repr(ref))
        self._ref_list.append(htypes.ref_list.ref_item(id, ref))

    def get_ref_list(self):
        return self._ref_list


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._module_registry = services.module_registry
        self._dynamic_ref_list_service = DynamicRefListService()
        services.management_ref_list = management_ref_list = ManagementRefList()
        self._dynamic_ref_list_service.register_ref_list(SERVER_MANAGEMENT_REF_LIST_ID, management_ref_list)
        self._init_dynamic_ref_list_service(services)

    def _init_dynamic_ref_list_service(self, services):
        iface_type_ref = services.type_resolver.reverse_resolve(htypes.ref_list.ref_list_service)
        service = htypes.hyper_ref.service(DYNAMIC_REF_LIST_SERVICE_ID, iface_type_ref)
        service_ref = services.ref_registry.register_object(service)
        services.service_registry.register(service_ref, self._resolve_dynamic_ref_list_service)

        dynamic_ref_list = htypes.ref_list.dynamic_ref_list(
            ref_list_service=service_ref,
            ref_list_id=SERVER_MANAGEMENT_REF_LIST_ID,
            )
        dynamic_ref_list_ref = services.ref_registry.register_object(dynamic_ref_list)

        ref_collector = services.ref_collector_factory()
        bundle = ref_collector.make_bundle([dynamic_ref_list_ref])
        ref_path = LOCAL_SERVER_DYNAMIC_REF_LIST_REF_PATH
        save_bundle_to_file(bundle, ref_path)
        log.info('Server management ref list ref is saved to: %s', ref_path)

    def _resolve_dynamic_ref_list_service(self):
        return self._dynamic_ref_list_service
