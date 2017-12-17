from ..common.interface import packet as packet_types
from ..common.url import Url
from .proxy_object import execute_get_request


REDIRECT_VIEW_ID = 'redirect'


def register_views(registry, services):
    registry.register(REDIRECT_VIEW_ID, resolve_redirect, services.iface_registry, services.remoting)

async def resolve_redirect(locale, handle, parent, iface_registry, remoting):
    url = Url.from_data(iface_registry, handle.redirect_to)
    handle = await execute_get_request(packet_types, remoting, url)
    return handle
