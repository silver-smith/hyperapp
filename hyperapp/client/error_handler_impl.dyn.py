import asyncio
from ..common.htypes import Field
from ..common.interface import core as core_types
from ..common.interface import text_object_types
from .module import Module
from .error_handler_hook import set_error_handler


ERROR_HANDLER_VIEW_ID = 'error_handler'
ERROR_HANDLER_CLASS_ID = 'error_handler'


def register_views(registry, services):
    registry.register(ERROR_HANDLER_VIEW_ID, this_module.resolve_error_handler)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._resources_manager = services.resources_manager
        self._error_handle_t = services.types.core.handle.register(
            ERROR_HANDLER_CLASS_ID, base=services.types.core.view_handle, fields=[
                Field('error', services.types.request.error),
                ])
        set_error_handler(self.error_handler)

    @asyncio.coroutine
    def resolve_error_handler(self, locale, state, parent):
        resource_id = ['error_message', state.error._class_id, locale]
        error_message_resource = self._resources_manager.resolve(resource_id)
        if error_message_resource:
            message = error_message_resource.message.format(error=state.error)
        else:
            message = 'Unexpected error: %s' % state.error._class_id
        obj = text_object_types.text_object('text', message)
        return core_types.obj_handle('text_view', obj)

    def error_handler(self, exception):
        # using intermediate handle is the simplest way to get currelt locale
        return self._error_handle_t(ERROR_HANDLER_VIEW_ID, exception)
