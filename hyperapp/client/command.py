import logging
import sys
import weakref

from ..common.htypes import resource_key_t
from ..common.ref import phony_ref
from .commander import Command, UnboundCommand
from .error_handler_hook import get_handle_for_error

log = logging.getLogger(__name__)


class WindowCommand(Command):

    @classmethod
    def from_command(cls, cmd, window):
        return cls(cmd.id, cmd.kind, cmd.resource_key, cmd.enabled, cmd, weakref.ref(window))

    def __init__(self, id, kind, resource_key, enabled, base_cmd, window_wr):
        Command.__init__(self, id, kind, resource_key, enabled)
        self._base_cmd = base_cmd
        self._window_wr = window_wr  # weak ref to class instance

    def __repr__(self):
        return 'WindowCommand(%r -> %r)' % (self.id, self._base_cmd)

    def get_view(self):
        return self._window_wr()

    async def run(self, *args, **kw):
        window = self._window_wr()
        if not window: return
        log.debug('WindowCommand.run: %r/%r, %r, (%s, %s)', self.id, self.kind, self._base_cmd, args, kw)
        handle = await self._base_cmd.run(*args, **kw)
        ## assert handle is None or isinstance(handle, tHandle), repr(handle)  # command can return only handle
        if handle:
            window.get_current_view().open(handle)


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
