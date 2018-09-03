import logging
import weakref
from ..common.htypes import Field, TRecord
from .command_class import Command, UnboundCommand
from .module import ClientModule
from .error_handler_hook import get_handle_for_error

log = logging.getLogger(__name__)


class ViewCommand(Command):

    @classmethod
    def from_command(cls, cmd, view):
        return cls(cmd.id, cmd.kind, cmd.resource_id, cmd.enabled, cmd, weakref.ref(view))

    def __init__(self, id, kind, resource_id, enabled, base_cmd, view_wr):
        Command.__init__(self, id, kind, resource_id, enabled)
        self._base_cmd = base_cmd
        self._view_wr = view_wr  # weak ref to class instance

    def __repr__(self):
        return 'ViewCommand(%r (base=%r) -> %s/%r)' % (self.id, self._base_cmd, id(self._view_wr()), self._view_wr())

    def get_view(self):
        return self._view_wr()

    def clone(self):
        return ViewCommand(self.id, self.kind, self.resource_id, self.enabled, self._base_cmd, self._window_wr)

    async def run(self, *args, **kw):
        view = self._view_wr()
        if not view: return
        log.debug('ViewCommand.run: %r/%r, %r, (%s, %s), view=%r', self.id, self.kind, self._base_cmd, args, kw, id(view))
        try:
            handle = await self._base_cmd.run(*args, **kw)
            ## assert handle is None or isinstance(handle, tHandle), repr(handle)  # command can return only handle
        except Exception as x:
            log.exception('Error running command %r:', self.id)
            handle = get_handle_for_error(x)
        if handle:
            view.open(handle)


class WindowCommand(Command):

    @classmethod
    def from_command(cls, cmd, window):
        return cls(cmd.id, cmd.kind, cmd.resource_id, cmd.enabled, cmd, weakref.ref(window))

    def __init__(self, id, kind, resource_id, enabled, base_cmd, window_wr):
        Command.__init__(self, id, kind, resource_id, enabled)
        self._base_cmd = base_cmd
        self._window_wr = window_wr  # weak ref to class instance

    def __repr__(self):
        return 'WindowCommand(%r -> %r)' % (self.id, self._base_cmd)

    def get_view(self):
        return self._window_wr()

    def clone(self):
        return WindowCommand(self.id, self.kind, self.resource_id, self.enabled, self._base_cmd, self._window_wr)

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
        module_name = class_method.__module__.split('.')[2]   # hyperapp.client.module [.submodule]
        class_name = class_method.__qualname__.split('.')[0]  # __qualname__ is 'Class.function'
        resource_id = ['client_module', module_name, class_name, 'command', self.id]
        return self.instantiate(self.wrap_method(class_method), resource_id)

    def instantiate(self, wrapped_class_method, resource_id):
        return UnboundCommand(self.id, self.kind, resource_id, self.enabled, wrapped_class_method)

    def wrap_method(self, method):
        return method
