import logging

from ..common.interface import hyper_ref as href_types
from ..common.local_server_paths import LOCAL_REF_RESOLVER_REF_PATH, save_bundle_to_file
from .command import command
from .object import Object
from .module import ServerModule

log = logging.getLogger(__name__)


REF_RESOLVER_SERVICE_ID = 'ref_resolver'
MODULE_NAME = 'ref_resolver_service'


class RefResolverService(Object):

    iface = href_types.ref_resolver
    #class_name = REF_RESOLVER_CLASS_NAME

    @classmethod
    def get_path(cls):
        return this_module.make_path(cls.class_name)

    def __init__(self, ref_resolver):
        Object.__init__(self)
        self._ref_resolver = ref_resolver

    def resolve(self, path):
        path.check_empty()
        return self

    @command('resolve_ref')
    def command_resolve_ref(self, request, ref):
        piece = self._ref_resolver.resolve_ref(ref)
        if not piece:
            raise href_types.unknown_ref_error(ref)
        return request.make_response_result(piece=piece)


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._ref_registry = services.ref_registry
        self._ref_collector_factory = services.ref_collector_factory
        self._encrypted_transport_ref = services.encrypted_transport_ref

    # depends on mapping being generated for ref_storage
    def init_phase3(self):
        service_ref = href_types.service_ref(['hyper_ref', 'ref_resolver'], REF_RESOLVER_SERVICE_ID, self._encrypted_transport_ref)
        ref_resolver_ref = self._ref_registry.register_object(href_types.service_ref, service_ref)
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle(ref_resolver_ref)
        save_bundle_to_file(bundle, LOCAL_REF_RESOLVER_REF_PATH)
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
