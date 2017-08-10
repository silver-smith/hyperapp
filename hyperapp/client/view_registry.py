import logging
import asyncio
from .registry import Registry
from .view import View

log = logging.getLogger(__name__)


MAX_REDIRECT_COUNT = 10


class ViewRegistry(Registry):

    def __init__(self, module_registry, iface_registry, remoting):
        Registry.__init__(self)
        self._module_registry = module_registry
        self._iface_registry = iface_registry
        self._remoting = remoting
        self._core_types = None

    def set_core_types(self, core_types):
        self._core_types = core_types

    @asyncio.coroutine
    def resolve(self, locale, handle, parent=None):
        assert isinstance(locale, str), repr(locale)
        assert isinstance(handle, self._core_types.handle), repr(handle)
        for i in range(MAX_REDIRECT_COUNT):
            rec = self._resolve(handle.view_id)
            log.info('producing view %r using %s(%s, %s)', handle.view_id, rec.factory, rec.args, rec.kw)
            view_or_handle = yield from rec.factory(locale, handle, parent, *rec.args, **rec.kw)
            assert isinstance(view_or_handle, (self._core_types.handle, View)), repr((handle.view_id, view_or_handle))  # must resolve to View or another handle
            if isinstance(view_or_handle, View):
                view_or_handle.init(self._module_registry)
                return view_or_handle
            handle = view_or_handle
        assert False, 'Too much redirections: %d' % i
