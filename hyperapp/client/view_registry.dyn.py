import logging
from hyperapp.common.registry import Registry
from hyperapp.common.module import Module
from hyperapp.client.view import View
from hyperapp.client.error_handler_hook import get_handle_for_error
from . import htypes

log = logging.getLogger(__name__)


MODULE_NAME = 'view_registry'
MAX_REDIRECT_COUNT = 10


class ViewRegistry(Registry):

    def __init__(self, module_command_registry):
        super().__init__()
        self._module_command_registry = module_command_registry

    async def resolve_async(self, locale, handle, parent=None):
        assert isinstance(locale, str), repr(locale)
        assert isinstance(handle, htypes.core.handle), repr(handle)
        for i in range(MAX_REDIRECT_COUNT):
            rec = self._resolve(handle.view_id)
            log.info('producing view %r using %s(%s, %s)', handle.view_id, rec.factory, rec.args, rec.kw)
            try:
                view_or_handle = await rec.factory(locale, handle, parent, *rec.args, **rec.kw)
                assert isinstance(view_or_handle, (htypes.core.handle, View)), repr((handle.view_id, view_or_handle))  # must resolve to View or another handle
            except Exception as x:
                log.exception('Error producing view %r:', handle.view_id)
                view_or_handle = get_handle_for_error(x)
            if isinstance(view_or_handle, View):
                view_or_handle.init(self._module_command_registry)
                return view_or_handle
            handle = view_or_handle
        assert False, 'Too much redirections: %d' % i


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.view_registry = ViewRegistry(services.module_command_registry)
