import logging

from ..common.interface import hyper_ref as href_types
from ..common.ref_collector import RefCollector
from .ref_resolver import RefResolver
from .module import ServerModule

log = logging.getLogger(__name__)


REF_RESOLVER_SERVICE_ID = 'ref_resolver'
MODULE_NAME = 'ref_resolver'


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        ref_storage = services.ref_storage
        self._ref_registry = ref_registry = services.ref_registry
        services.ref_resolver = self._ref_resolver = RefResolver(ref_registry, ref_storage)
        self._type_registry_registry = services.type_registry_registry
        self._encrypted_transport_ref = services.encrypted_transport_ref

    # depends on mapping being generated for ref_storage
    def init_phase3(self):
        service_ref = href_types.service_ref(REF_RESOLVER_SERVICE_ID, self._encrypted_transport_ref)
        ref_resolver_ref = self._ref_registry.register_object(href_types.service_ref, service_ref)
        ref_collector = RefCollector(self._type_registry_registry, self._ref_resolver)
        referred_list = ref_collector.collect_referred(ref_resolver_ref)
        parcel = href_types.parcel(ref_resolver_ref, referred_list)
        save_parcel_to_file(parcel, LOCAL_REF_RESOLVER_REF_PATH)
        log.info('Ref resolver ref is saved to %s', LOCAL_REF_RESOLVER_REF_PATH)

#    def init_phase2(self):
#        public_key = self._server.get_public_key()
#        url = Url(RefResolver.iface, public_key, RefResolver.get_path())
#        url_with_routes = url.clone_with_routes(self._tcp_server.get_routes())
#        url_path = save_url_to_file(url_with_routes, LOCAL_REF_RESOLVER_URL_PATH)
#        log.info('Ref resolver url is saved to: %s', url_path)

#    def resolve(self, iface, path):
#        objname = path.pop_str()
#        if objname == RefResolver.class_name:
#            return RefResolver(self._server, self._ref_storage).resolve(path)
#        path.raise_not_found()
