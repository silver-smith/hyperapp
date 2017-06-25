from ..common.interface import core as core_types
from ..common.interface import text_object_types
from .module import Module
from .error_handler_hook import set_error_handler


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        set_error_handler(self.error_handler)

    def error_handler(self, exception):
        obj = text_object_types.text_object('text', 'Unexpected error: %s' % exception._class_id)
        return core_types.obj_handle('text_view', obj)
