import logging
import traceback
from .registry import Registry
from .view import View
from .error_handler_hook import get_handle_for_error

log = logging.getLogger(__name__)


MAX_REDIRECT_COUNT = 10


class ViewRegistry(Registry):

    def __init__(self, module_registry, iface_registry):
        Registry.__init__(self)
        self._module_registry = module_registry
        self._iface_registry = iface_registry
        self._core_types = None

    def set_core_types(self, core_types):
        self._core_types = core_types

    async def resolve(self, locale, handle, parent=None):
        assert isinstance(locale, str), repr(locale)
        assert isinstance(handle, self._core_types.handle), repr(handle)
        for i in range(MAX_REDIRECT_COUNT):
            rec = self._resolve(handle.view_id)
            log.info('producing view %r using %s(%s, %s)', handle.view_id, rec.factory, rec.args, rec.kw)
            try:
                view_or_handle = await rec.factory(locale, handle, parent, *rec.args, **rec.kw)
                assert isinstance(view_or_handle, (self._core_types.handle, View)), repr((handle.view_id, view_or_handle))  # must resolve to View or another handle
            except Exception as x:
                traceback.print_exc()
                view_or_handle = get_handle_for_error(x)
            if isinstance(view_or_handle, View):
                view_or_handle.init(self._module_registry)
                return view_or_handle
            handle = view_or_handle
        assert False, 'Too much redirections: %d' % i
