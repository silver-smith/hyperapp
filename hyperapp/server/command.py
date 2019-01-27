import logging
import weakref
from ..common.util import is_list_inst
#from ..common.htypes import tCommand
from ..common import command as common_command

log = logging.getLogger(__name__)


class BoundCommand(common_command.Command):

    def __init__(self, id, kind, resource_id, class_method, inst_wr):
        common_command.Command.__init__(self, id)
        assert isinstance(kind, str), repr(kind)
        assert is_list_inst(resource_id, str), repr(resource_id)
        self.id = id
        self.kind = kind
        self.resource_id = resource_id
        self._class_method = class_method
        self._inst_wr = inst_wr  # weak ref to class instance

    def __repr__(self):
        return 'BoundCommand(%r/%r -> %r)' % (self.id, self.kind, self._inst_wr)

    def to_data(self):
        return tCommand(self.id, self.kind, self.resource_id)

    def run(self, request):
        inst = self._inst_wr()
        if not inst: return  # inst is deleteddeleted
        log.debug('BoundCommand.run: %s, %r/%r, %r', self, self.id, self.kind, inst)
        return self._class_method(inst, request, **request.params._asdict())


class UnboundCommand(common_command.Command):

    def __init__(self, id, kind, class_method):
        assert kind is None or isinstance(kind, str), repr(kind)
        common_command.Command.__init__(self, id)
        self.kind = kind
        self.resource_id = None  # set by CommanderMetaClass
        self._class_method = class_method

    # Element may be returned from classmethod, for which commands are unbound
    def to_data(self):
        return tCommand(self.id, self.kind, self.resource_id)

    def bind(self, inst, kind):
        if self.kind is not None:
            kind = self.kind
        return BoundCommand(self.id, kind, self.resource_id, self._class_method, weakref.ref(inst))


# decorator for object methods
class command(object):

    def __init__(self, id, kind=None):
        assert isinstance(id, str), repr(id)
        assert kind is None or isinstance(kind, str), repr(kind)
        self.id = id
        self.kind = kind

    def __call__(self, class_method):
        return UnboundCommand(self.id, self.kind, class_method)


class CommanderMetaClass(type):

    def __new__(meta_cls, name, bases, members):
        cls = type.__new__(meta_cls, name, bases, members)
        for name, attr in members.items():
            if not isinstance(attr, UnboundCommand): continue
            iface = getattr(cls, 'iface', None)
            assert iface, '"iface" attribute is not set for class %r' % cls.__name__
            #attr.resource_id = ['interface', iface.iface_id, 'command', attr.id]
        return cls


class Commander(object, metaclass=CommanderMetaClass):

    def __init__(self, commands_kind):
        if hasattr(self, '_commands'):  # multiple inheritance hack
            return  # do not populate _commands twice
        self._commands_kind = commands_kind
        self._commands = []  # BoundCommand list
        for name in dir(self):
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
        return None

    def get_commands(self):
        return [cmd for cmd in self._commands if cmd.kind == self._commands_kind]
