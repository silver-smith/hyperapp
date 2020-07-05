import logging
import sys
import weakref

from ..common.htypes import resource_key_t
from ..common.ref import phony_ref
from .commander import Command, UnboundCommand
from .error_handler_hook import get_handle_for_error

log = logging.getLogger(__name__)


# decorator for view methods
class command(object):

    def __init__(self, id, kind=None, enabled=True):
        assert isinstance(id, str), repr(id)
        assert kind is None or isinstance(kind, str), repr(kind)
        assert isinstance(enabled, bool), repr(enabled)
        self.id = id
        self.kind = kind
        self.enabled = enabled

    def __call__(self, class_method):
        module_name = class_method.__module__
        module = sys.modules[module_name]
        module_ref = module.__dict__.get('__module_ref__') or phony_ref(module_name.split('.')[-1])
        class_name = class_method.__qualname__.split('.')[0]  # __qualname__ is 'Class.function'
        resource_key = resource_key_t(module_ref, [class_name, 'command', self.id])
        return self.instantiate(self.wrap_method(class_method), resource_key)

    def instantiate(self, wrapped_class_method, resource_key):
        return UnboundCommand(self.id, self.kind, resource_key, self.enabled, wrapped_class_method)

    def wrap_method(self, method):
        return method
