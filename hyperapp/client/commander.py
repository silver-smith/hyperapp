import logging
import inspect
import weakref
import abc

from ..common.util import is_list_inst
from ..common.htypes import resource_key_t

_log = logging.getLogger(__name__)


# returned from Object.get_commands
class Command(metaclass=abc.ABCMeta):

    def __init__(self, id, kind, resource_key, enabled=True):
        assert isinstance(kind, str), repr(kind)
        assert isinstance(resource_key, resource_key_t), repr(resource_key)
        assert isinstance(enabled, bool), repr(enabled)
        self.id = id
        self.kind = kind
        self.resource_key = resource_key
        self.enabled = enabled

    def __repr__(self):
        return '%s(id=%r kind=%r)' % (self.__class__.__name__, self.id, self.kind)

    def is_enabled(self):
        return self.enabled

    def set_enabled(self, enabled):
        if enabled == self.enabled: return
        self.enabled = enabled
        object = self.get_view()
        _log.debug('-- Command.set_enabled %r object=%r', self.id, object)
        if object:
            object._notify_object_changed()

    def enable(self):
        self.set_enabled(True)

    def disable(self):
        self.set_enabled(False)
    
    @abc.abstractmethod
    async def run(self, *args, **kw):
        pass


class BoundCommand(Command):

    def __init__(
            self,
            id,
            kind,
            resource_key,
            enabled,
            class_method,
            inst_wr,
            args=None,
            kw=None,
            wrapper=None,
            piece=None,
            params_editor=None,
            params_subst=None,
            ):
        Command.__init__(self, id, kind, resource_key, enabled)
        self._class_method = class_method
        self._inst_wr = inst_wr  # weak ref to class instance
        self._args = args or ()
        self._kw = kw or {}
        self._wrapper = wrapper
        self._piece = piece  # piece this instance created from
        self._params_editor = params_editor
        self._params_subst = params_subst

    def __repr__(self):
        return (f"BoundCommand(id={self.id} kind={self.kind} inst={self._inst_wr}"
                f" args={self._args} kw={self._kw} wrapper={self._wrapper} pe={self._piece}/{self._params_editor})")

    def get_view(self):
        return self._inst_wr()

    async def run(self, *args, **kw):
        inst = self._inst_wr()
        if not inst:
            return  # instance we bound to is already deleted
        if self._params_subst:
            _log.info("Command: subst params: (%r) args=%r kw=%r", self, args, kw)
            args, kw = self._params_subst(*self._args, *args, **self._kw, **kw)
        else:
            args = (*self._args, *args)
            kw = {**self._kw, **kw}
        if self._more_params_are_required(*args, **kw):
            _log.info("Command: run param editor: (%r) args=%r kw=%r", self, args, kw)
            assert self._params_editor  # More parameters are required, but param editor is not set
            result = await self._params_editor(self._piece, self, args, kw)
        else:
            _log.info("Command: run: (%r) args=%r kw=%r", self, args, kw)
            if inspect.iscoroutinefunction(self._class_method):
                result = await self._class_method(inst, *args, **kw)
            else:
                result = self._class_method(inst, *args, **kw)
        if result is None:
            return
        if self._wrapper:
            result = await self._wrapper(result)
        return result

    def with_(self, **kw):
        old_kw = dict(
            id=self.id,
            kind=self.kind,
            resource_key=self.resource_key,
            enabled=self.enabled,
            class_method=self._class_method,
            inst_wr=self._inst_wr,
            args=self._args,
            kw=self._kw,
            wrapper=self._wrapper,
            piece=self._piece,
            params_editor=self._params_editor,
            params_subst=self._params_subst,
            )
        all_kw = {**old_kw, **kw}
        return BoundCommand(**all_kw)

    def partial(self, *args, **kw):
        return self.with_(args=args, kw=kw)

    def bound_arguments(self, *args, **kw):
        signature = inspect.signature(self._class_method)
        inst = self._inst_wr()
        assert inst  # instance we bound to is already deleted
        return signature.bind_partial(inst, *args, **kw)

    def _more_params_are_required(self, *args, **kw):
        signature = inspect.signature(self._class_method)
        try:
            inst = None
            signature.bind(inst, *args, **kw)
            return False
        except TypeError as x:
            if str(x).startswith('missing a required argument: '):
                _log.info("More params are required: %s", x)
                return True
            else:
                raise


class UnboundCommand(object):

    def __init__(self, id, kind, resource_key, enabled, class_method):
        assert isinstance(id, str), repr(id)
        assert kind is None or isinstance(kind, str), repr(kind)
        assert isinstance(resource_key, resource_key_t), repr(resource_key)
        assert isinstance(enabled, bool), repr(enabled)
        self.id = id
        self.kind = kind
        self._resource_key = resource_key
        self.enabled = enabled
        self._class_method = class_method

    def bind(self, inst, kind):
        if self.kind is not None:
            kind = self.kind
        return self._bind(weakref.ref(inst), kind)

    def _bind(self, inst_wr, kind):
        return BoundCommand(self.id, kind, self._resource_key, self.enabled, self._class_method, inst_wr)


class Commander(object):

    def __init__(self, commands_kind):
        if hasattr(self, '_commands'):  # multiple inheritance hack
            return  # do not populate _commands twice
        self._commands_kind = commands_kind
        self._commands = []  # BoundCommand list
        for name in dir(self):
            cls = type(self)
            if hasattr(cls, name) and type(getattr(cls, name)) is property:
                continue  # avoid to call properties as we are not yet fully constructed
            attr = getattr(self, name)
            if not isinstance(attr, UnboundCommand): continue
            bound_cmd = attr.bind(self, commands_kind)
            setattr(self, name, bound_cmd)  # set_enabled must change command for this view, not for all of them
            self._commands.append(bound_cmd)

    def get_command(self, command_id):
        for command in self._commands:
            assert isinstance(command, BoundCommand), repr(command)
            if command.id == command_id:
                return command
        raise KeyError(f"{self!r}: Unknown command: {command_id}")

    def get_command_list(self, kinds=None):
        if kinds is None:
            kinds = {self._commands_kind}
        return [cmd for cmd in self.get_all_command_list() if cmd.kind in kinds]

    def get_all_command_list(self):
        return self._commands
