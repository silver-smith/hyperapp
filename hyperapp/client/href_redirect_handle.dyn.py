import asyncio


REDIRECT_VIEW_ID = 'href_redirect'


def register_views(registry, services):
    registry.register(REDIRECT_VIEW_ID, resolve_redirect, services.iface_registry, services.remoting)

@asyncio.coroutine
def resolve_redirect(locale, handle, parent, iface_registry, remoting):
    href = handle.href
    assert 0, href
