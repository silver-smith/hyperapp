from hyperapp.common.htypes import Field
from hyperapp.client.module import ClientModule
from hyperapp.client.error_handler_hook import set_error_handler
from . import htypes


MODULE_NAME = 'ereror_handler_impl'

ERROR_HANDLER_VIEW_ID = 'error_handler'
ERROR_HANDLER_CLASS_ID = 'error_handler'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._resource_resolver = services.resource_resolver
        self._error_handle_t = htypes.core.handle.register(
            ERROR_HANDLER_CLASS_ID, base=htypes.core.view_handle, fields=[
                Field('error', htypes.error.error),
                ])
        services.view_registry.register(ERROR_HANDLER_VIEW_ID, self.resolve_error_handler)
        set_error_handler(self.error_handler)

    async def resolve_error_handler(self, locale, state, parent):
        resource_id = ['error_message', state.error._class_id, locale]
        error_message_resource = self._resource_resolver.resolve(resource_id)
        if error_message_resource:
            message = error_message_resource.message.format(error=state.error)
        else:
            message = 'Unexpected error: %s' % state.error._class_id
        # somehow this state got stuck forever, holding all objects in it's traceback, including views subscribed to events
        state.error.__traceback__ = None
        obj = htypes.text_object.text_object('text', message)
        return htypes.core.obj_handle('text_view', obj)

    def error_handler(self, exception):
        if not isinstance(exception, htypes.error.error):
            exception = htypes.error.unknown_client_error()
        # using intermediate handle is the simplest way to get current locale
        return self._error_handle_t(ERROR_HANDLER_VIEW_ID, exception)
