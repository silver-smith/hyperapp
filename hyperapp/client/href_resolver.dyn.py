import os.path
import logging
from ..common.interface import hyper_ref as href_types
from ..common.url import UrlWithRoutes
from ..common.local_server_paths import LOCAL_HREF_RESOLVER_URL_PATH
from .registry import Registry
from .module import Module

log = logging.getLogger(__name__)


class HRefResolver(object):

    def __init__(self, href_registry, href_object_registry, href_resolver_proxy):
        self._href_registry = href_registry
        self._href_object_registry = href_object_registry
        self._href_resolver_proxy = href_resolver_proxy

    async def resolve_href_to_handle(self, href):
        object = self._href_registry.resolve(href)
        if not object:
            object = await self.resolve_href(href)
            self._href_registry.register(href, object)
        assert object, repr(object)
        log.debug('href resolver: href resolved to %r', object)
        handle = await self._href_object_registry.resolve(object)
        assert handle, repr(handle)
        log.debug('href resolver: href object resolved to handle %r', handle)
        return handle

    async def resolve_href(self, href):
        result = await self._href_resolver_proxy.resolve_href(href)
        return result.href_object

    async def resolve_service_ref(self, service_ref):
        result = await self._href_resolver_proxy.resolve_service_ref(service_ref)
        return result.service


class HRefRegistry(object):

    def __init__(self):
        self._registry = {}

    def register(self, href, href_object):
        assert isinstance(href, href_types.href), repr(href)
        assert isinstance(href_object, href_types.href_object), repr(href_object)
        existing_object = self._registry.get(href)
        if existing_object:
            assert href_object == existing_object, repr((existing_object, href_object))  # new object does not match existing one
        self._registry[href] = href_object

    def resolve(self, href):
        return self._registry.get(href)


class HRefObjectRegistry(Registry):

    async def resolve(self, href_object):
        tclass = href_types.href_object.get_object_class(href_object)
        rec = self._resolve(tclass.id)
        log.info('producing href object %r using %s(%s, %s)', tclass.id, rec.factory, rec.args, rec.kw)
        return (await rec.factory(href_object, *rec.args, **rec.kw))


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._remoting = services.remoting
        self._href_registry = HRefRegistry()
        url_path = os.path.expanduser(LOCAL_HREF_RESOLVER_URL_PATH)
        with open(url_path) as f:
            url = UrlWithRoutes.from_str(services.iface_registry, f.read())
        href_resolver_proxy = services.proxy_factory.from_url(url)
        services.href_registry = self._href_registry
        services.href_object_registry = HRefObjectRegistry()
        services.href_resolver = HRefResolver(self._href_registry, services.href_object_registry, href_resolver_proxy)
