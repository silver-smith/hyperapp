import logging
import asyncio
from ..common.url import Url
from .registry import Registry
from .view import View
from .proxy_object import execute_get_request

log = logging.getLogger(__name__)


class ViewRegistry(Registry):

    def __init__( self, iface_registry, remoting ):
        Registry.__init__(self)
        self._iface_registry = iface_registry
        self._remoting = remoting

    @asyncio.coroutine
    def resolve( self, locale, handle, parent=None ):
        assert isinstance(locale, str), repr(locale)
        assert isinstance(handle, tHandle), repr(handle)
        if isinstance(handle, tRedirectHandle):
            url = Url.from_data(self._iface_registry, handle.redirect_to)
            handle = yield from execute_get_request(self._remoting, url)
        rec = self._resolve(handle.view_id)
        log.info('producing view %r using %s(%s, %s)', handle.view_id, rec.factory, rec.args, rec.kw)
        view = yield from rec.factory(locale, handle, parent, *rec.args, **rec.kw)
        assert isinstance(view, View), repr((handle.view_id, view))  # must resolve to View
        return view
