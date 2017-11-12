import asyncio
import os.path
import logging
from ..common.interface import hyper_ref as href_types
from ..common.url import UrlWithRoutes
from ..common.local_server_paths import LOCAL_HREF_RESOLVER_URL_PATH
from .registry import Registry
from .module import Module

log = logging.getLogger(__name__)


class HRefResolver(object):

    def __init__(self, href_object_registry, href_resolver_proxy):
        self._href_object_registry = href_object_registry
        self._href_resolver_proxy = href_resolver_proxy

    @asyncio.coroutine
    def resolve_href_to_handle(self, href):
        object = yield from self.resolve_href(href)
        assert object, repr(object)
        log.debug('href resolver: href resolved to %r', object)
        handle = yield from self._href_object_registry.resolve(object)
        assert handle, repr(handle)
        log.debug('href resolver: href object resolved to handle %r', handle)
        return handle

    @asyncio.coroutine
    def resolve_href(self, href):
        result = yield from self._href_resolver_proxy.resolve_href(href)
        return result.href_object

    @asyncio.coroutine
    def resolve_service_ref(self, service_ref):
        result = yield from self._href_resolver_proxy.resolve_service_ref(service_ref)
        return result.service


class HRefObjectRegistry(Registry):

    @asyncio.coroutine
    def resolve(self, href_object):
        tclass = href_types.href_object.get_object_class(href_object)
        rec = self._resolve(tclass.id)
        log.info('producing href object %r using %s(%s, %s)', tclass.id, rec.factory, rec.args, rec.kw)
        return (yield from rec.factory(href_object, *rec.args, **rec.kw))


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._remoting = services.remoting
        url_path = os.path.expanduser(LOCAL_HREF_RESOLVER_URL_PATH)
        with open(url_path) as f:
            url = UrlWithRoutes.from_str(services.iface_registry, f.read())
        proxy = services.proxy_factory.from_url(url)
        services.href_object_registry = HRefObjectRegistry()
        services.href_resolver = HRefResolver(services.href_object_registry, proxy)
