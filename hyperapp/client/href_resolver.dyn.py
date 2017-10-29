import asyncio
import os.path
from ..common.interface import hyper_ref as href_types
from ..common.url import UrlWithRoutes
from .registry import Registry
from .module import Module


HREF_RESOLVER_URL_PATH = '~/.local/share/hyperapp/common/href_resolver.url'


class HRefResolver(object):

    def __init__(self, href_resolver_proxy):
        self._href_resolver_proxy = href_resolver_proxy

    @asyncio.coroutine
    def resolve_href(self, href):
        result = yield from self._href_resolver_proxy.resolve_href(href)
        return result.href_object


class HRefObjectRegistry(Registry):

    def resolve(self, href_object):
        tclass = href_types.href_object.resolve_obj(href_object)
        rec = self._resolve(tclass.id)
        log.info('producing href object %r using %s(%s, %s)', tclass.id, rec.factory, rec.args, rec.kw)
        return rec.factory(href_object, *rec.args, **rec.kw)


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
