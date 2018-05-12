import logging

from ..common.interface import hyper_ref as href_types
from ..common.url import UrlWithRoutes
from ..common.packet_coders import packet_coders
from ..common.ref import make_capsule, make_ref
from ..common.local_server_paths import LOCAL_REF_RESOLVER_REF_PATH, load_bundle_from_file
from .capsule_registry import CapsuleRegistry, CapsuleResolver
from .module import Module

log = logging.getLogger(__name__)


class RefResolver(object):

    def __init__(self, type_registry_registry, ref_registry, ref_resolver_proxy):
        self._type_registry_registry = type_registry_registry
        self._ref_registry = ref_registry
        self._ref_resolver_proxy = ref_resolver_proxy

    async def resolve_ref(self, ref):
        capsule = self._ref_registry.resolve(ref)
        if not capsule:
            result = await self._ref_resolver_proxy.resolve_ref(ref)
            capsule = result.capsule
            self._ref_registry.register(ref, capsule)
        log.debug('ref resolver: ref resolved to %r', capsule)
        assert capsule, repr(capsule)
        return capsule

    async def resolve_ref_to_object(self, ref):
        capsule = await self.resolve_ref(ref)
        t = self._type_registry_registry.resolve_type(capsule.full_type_name)
        return packet_coders.decode(capsule.encoding, capsule.encoded_object, t)


class RefRegistry(object):

    def __init__(self):
        self._registry = {}

    # check if capsule is matching if ref is already registered
    def register(self, ref, capsule):
        assert isinstance(ref, href_types.ref), repr(ref)
        assert isinstance(capsule, href_types.capsule), repr(capsule)
        existing_capsule = self._registry.get(ref)
        if existing_capsule:
            assert capsule == existing_capsule, repr((existing_capsule, capsule))  # new capsule does not match existing one
        self._registry[ref] = capsule

    def register_new_object(self, t, object):
        capsule = make_capsule(t, object)
        ref = make_ref(capsule)
        self.register(ref, capsule)
        return ref

    def register_capsule_list(self, capsule_list):
        for capsule in capsule_list:
            ref = make_ref(capsule)
            self.register(ref, capsule)

    def resolve(self, ref):
        return self._registry.get(ref)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._remoting = services.remoting
        self._ref_registry = RefRegistry()
        bundle = load_bundle_from_file(LOCAL_REF_RESOLVER_REF_PATH)
        self._ref_registry.register_capsule_list(bundle.capsule_list)

        with open(url_path) as f:
            url = UrlWithRoutes.from_str(services.iface_registry, f.read())
        ref_resolver_proxy = services.proxy_factory.from_url(url)
        services.ref_registry = self._ref_registry
        services.ref_resolver = ref_resolver = RefResolver(services.type_registry_registry, self._ref_registry, ref_resolver_proxy)
        services.handle_registry = handle_registry = CapsuleRegistry('handle', services.type_registry_registry)
        services.handle_resolver = CapsuleResolver(ref_resolver, handle_registry)
