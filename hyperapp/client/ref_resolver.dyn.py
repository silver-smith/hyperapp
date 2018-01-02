import os.path
import logging
from ..common.interface import hyper_ref as href_types
from ..common.url import UrlWithRoutes
from ..common.packet_coders import packet_coders
from ..common.local_server_paths import LOCAL_REF_RESOLVER_URL_PATH
from .registry import Registry
from .module import Module

log = logging.getLogger(__name__)


class RefResolver(object):

    def __init__(self, ref_registry, referred_registry, ref_resolver_proxy):
        self._ref_registry = ref_registry
        self._referred_registry = referred_registry
        self._ref_resolver_proxy = ref_resolver_proxy

    async def resolve_ref_to_handle(self, ref):
        referred = self._ref_registry.resolve(ref)
        if not referred:
            referred = await self.resolve_ref(ref)
            self._ref_registry.register(ref, referred)
        assert referred, repr(referred)
        log.debug('ref resolver: ref resolved to %r', referred)
        handle = await self._referred_registry.resolve(referred)
        assert handle, repr(handle)
        log.debug('ref resolver: referred resolved to handle %r', handle)
        return handle

    async def resolve_ref(self, ref):
        result = await self._ref_resolver_proxy.resolve_ref(ref)
        return result.referred

    async def resolve_ref_to_object(self, ref, t):
        referred = await self.resolve_ref(ref)
        return packet_coders.decode(referred.encoding, referred.encoded_object, t)


class RefRegistry(object):

    def __init__(self):
        self._registry = {}

    # check if referred is matching if ref is already registered
    def register(self, ref, referred):
        assert isinstance(ref, href_types.ref), repr(ref)
        assert isinstance(referred, href_types.referred), repr(referred)
        existing_referred = self._registry.get(ref)
        if existing_referred:
            assert referred == existing_referred, repr((existing_referred, referred))  # new referred does not match existing one
        self._registry[ref] = referred

    def resolve(self, ref):
        return self._registry.get(ref)


class ReferredRegistry(Registry):

    def register(self, full_type_name, factory, *args, **kw):
        assert isinstance(full_type_name, str), repr(full_type_name)
        super().register(tuple(full_type_name.split('.')), factory, *args, **kw)
        
    async def resolve(self, referred):
        rec = self._resolve(tuple(referred.full_type_name))
        log.info('producing referred %s using %s(%s, %s)', '.'.join(referred.full_type_name), rec.factory, rec.args, rec.kw)
        return (await rec.factory(referred, *rec.args, **rec.kw))


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._remoting = services.remoting
        self._ref_registry = RefRegistry()
        url_path = os.path.expanduser(LOCAL_REF_RESOLVER_URL_PATH)
        with open(url_path) as f:
            url = UrlWithRoutes.from_str(services.iface_registry, f.read())
        ref_resolver_proxy = services.proxy_factory.from_url(url)
        services.ref_registry = self._ref_registry
        services.referred_registry = ReferredRegistry()
        services.ref_resolver = RefResolver(self._ref_registry, services.referred_registry, ref_resolver_proxy)
