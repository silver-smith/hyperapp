import logging

from ..common.interface import hyper_ref as href_types
from ..common.local_server_paths import LOCAL_REF_RESOLVER_REF_PATH, save_bundle_to_file
from .module import ServerModule

log = logging.getLogger(__name__)


REF_RESOLVER_SERVICE_ID = 'ref_resolver'
MODULE_NAME = 'ref_resolver_service'


class RefResolverService(object):

    def __init__(self, ref_resolver):
        self._ref_resolver = ref_resolver

    def rpc_resolve_ref(self, request, ref):
        capsule = self._ref_resolver.resolve_ref(ref)
        if not capsule:
            raise href_types.unknown_ref_error(ref)
        return request.make_response_result(capsule=capsule)


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._ref_registry = services.ref_registry
        self._ref_resolver = services.ref_resolver
        self._service_registry = services.service_registry
        self._ref_collector_factory = services.ref_collector_factory

    # depends on mapping being generated for ref_storage
    def init_phase3(self, services):
        service = href_types.service(REF_RESOLVER_SERVICE_ID, ['hyper_ref', 'ref_resolver'])
        service_ref = self._ref_registry.register_object(service)
        self._service_registry.register(service_ref, RefResolverService, self._ref_resolver)
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle([service_ref])
        ref_path = LOCAL_REF_RESOLVER_REF_PATH
        save_bundle_to_file(bundle, ref_path)
        log.info('Ref resolver ref is saved to %s', ref_path)

#    def init_phase2(self, services):
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
