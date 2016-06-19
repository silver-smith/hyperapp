import asyncio
from ..common.htypes import tHandle, tRedirectHandle, iface_registry
from ..common.endpoint import Url
from .view import View
from .proxy_object import execute_get_request


class ViewRegistry(object):

    def __init__( self ):
        self.registry = {}  # view id -> ctr

    def register( self, view_id, handle_ctr ):
        assert view_id not in self.registry, repr(view_id)  # Duplicate id
        self.registry[view_id] = handle_ctr

    def is_view_registered( self, view_id ):
        return view_id in self.registry

    @asyncio.coroutine
    def resolve( self, handle, parent=None ):
        assert isinstance(handle, tHandle), repr(handle)
        if isinstance(handle, tRedirectHandle):
            url = Url.from_data(iface_registry, handle.redirect_to)
            handle = yield from execute_get_request(url)
        ctr = self.registry[handle.view_id]
        view = yield from ctr(handle, parent)
        assert isinstance(view, View), repr((handle.view_id, view))  # must resolve to View
        return view


view_registry = ViewRegistry()
