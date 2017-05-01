import asyncio
from ..common.url import Url
from .proxy_object import execute_get_request


REDIRECT_VIEW_ID = 'redirect'


def register_views(registry, services):
    registry.register(REDIRECT_VIEW_ID, resolve_redirect, services.request_types, services.iface_registry, services.remoting)

@asyncio.coroutine
def resolve_redirect(locale, handle, parent, request_types, iface_registry, remoting):
    url = Url.from_data(iface_registry, handle.redirect_to)
    result = yield from execute_get_request(request_types, remoting, url)
    return result.handle
