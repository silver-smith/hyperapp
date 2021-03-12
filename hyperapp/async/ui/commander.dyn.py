import logging
import inspect
import weakref
import abc
import sys

from hyperapp.common.util import is_list_inst
from hyperapp.common.htypes import phony_ref, resource_key_t

_log = logging.getLogger(__name__)


def resource_key_of_class_method(class_method, *resource_path):
    module_name = class_method.__module__
    module = sys.modules[module_name]
    module_ref = module.__dict__.get('__module_ref__') or phony_ref(module_name.split('.')[-1])
    class_name = class_method.__qualname__.split('.')[0]  # __qualname__ is 'Class.function'
    return resource_key_t(module_ref, [class_name, *resource_path])


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
            params_subst=None,
            ):
        Command.__init__(self, id, kind, resource_key, enabled)
        self._class_method = class_method
        self._inst_wr = inst_wr  # weak ref to class instance
        self._args = args or ()
        self._kw = kw or {}
        self._wrapper = wrapper
        self._params_subst = params_subst

    def __repr__(self):
        return (f"BoundCommand(id={self.id} kind={self.kind} inst={self._inst_wr}"
                f" args={self._args} kw={self._kw} wrapper={self._wrapper})")

    def get_view(self):
        return self._inst_wr()

    async def run(self, *args, **kw):
        inst = self._inst_wr()
        if not inst:
            return  # instance we bound to is already deleted
        if self._params_subst:
            _log.info("BoundCommand: subst params: (%r) args=%r kw=%r", self, args, kw)
            full_args, full_kw = self._params_subst(*self._args, *args, **self._kw, **kw)
        else:
            full_args = (*self._args, *args)
            full_kw = {**self._kw, **kw}
        result = await self._run_impl(inst, full_args, full_kw)
        _log.info("BoundCommand: run result: %r", result)
        return (await self._wrap_result(result))

    async def run_with_full_params(self, *args, **kw):
        inst = self._inst_wr()
        if not inst:
            return  # instance we bound to is already deleted
        _log.info("BoundCommand: run with full params:")
        result = await self._run_impl(inst, args, kw)
        _log.info("BoundCommand: run result: %r", result)
        return (await self._wrap_result(result))

    async def _run_impl(self, inst, args, kw):
        _log.info("Command: run: (%r) args=%r kw=%r", self, args, kw)
        if inspect.iscoroutinefunction(self._class_method):
            return (await self._class_method(inst, *args, **kw))
        else:
            return self._class_method(inst, *args, **kw)

    async def _wrap_result(self, result):
        if result is None:
            return
        if self._wrapper:
            _log.info("Command: wrap result with %r", self._wrapper)
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
            params_subst=self._params_subst,
            )
        all_kw = {**old_kw, **kw}
        return BoundCommand(**all_kw)

    def partial(self, *args, **kw):
        return self.with_(args=args, kw=kw)


class UnboundCommand(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def bind(self, inst, kind):
        pass


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
            if command.id == command_id:
                return command
        raise KeyError(f"{self!r}: Unknown command: {command_id}")

    def get_command_list(self, kinds=None):
        if kinds is None:
            kinds = {self._commands_kind}
        return [cmd for cmd in self.get_all_command_list() if cmd.kind in kinds]

    def get_all_command_list(self):
        return self._commands
