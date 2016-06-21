import logging
import asyncio
from ..common.htypes import tHandle, tRedirectHandle, iface_registry
from ..common.endpoint import Url
from .registry import Registry
from .view import View
from .proxy_object import execute_get_request

log = logging.getLogger(__name__)


class ViewRegistry(Registry):

    @asyncio.coroutine
    def resolve( self, handle, parent=None ):
        assert isinstance(handle, tHandle), repr(handle)
        if isinstance(handle, tRedirectHandle):
            url = Url.from_data(iface_registry, handle.redirect_to)
            handle = yield from execute_get_request(url)
        rec = self._resolve(handle.view_id)
        log.info('producing view %r using %s(%s, %s)', handle.view_id, rec.factory, rec.args, rec.kw)
        view = yield from rec.factory(handle, parent, *rec.args, **rec.kw)
        assert isinstance(view, View), repr((handle.view_id, view))  # must resolve to View
        return view


view_registry = ViewRegistry()
