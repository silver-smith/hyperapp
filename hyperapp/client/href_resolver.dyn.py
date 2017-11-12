import asyncio
import os.path
import logging
from ..common.interface import hyper_ref as href_types
from ..common.url import UrlWithRoutes
from ..common.local_server_paths import HREF_RESOLVER_URL_PATH
from .registry import Registry
from .module import Module

log = logging.getLogger(__name__)


class HRefResolver(object):

    def __init__(self, href_resolver_proxy):
        self._href_resolver_proxy = href_resolver_proxy

    @asyncio.coroutine
    def resolve_href(self, ref):
        result = yield from self._href_resolver_proxy.resolve_href(ref)
        return result.href_object

    @asyncio.coroutine
    def resolve_service_ref(self, ref):
        result = yield from self._href_resolver_proxy.resolve_service_ref(ref)
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
        url_path = os.path.expanduser(HREF_RESOLVER_URL_PATH)
        with open(url_path) as f:
            url = UrlWithRoutes.from_str(services.iface_registry, f.read())
        proxy = services.proxy_factory.from_url(url)
        services.href_resolver = HRefResolver(proxy)
        services.href_object_registry = HRefObjectRegistry()
