import logging
import weakref
from ..common.util import is_list_inst
from ..common.htypes import tCommand

log = logging.getLogger(__name__)


class BoundCommand(object):

    def __init__( self, id, kind, resource_id, is_default_command, class_method, inst_wr, args=None ):
        assert isinstance(id, str), repr(id)
        assert isinstance(kind, str), repr(kind)
        assert isinstance(resource_id, str), repr(resource_id)
        assert isinstance(is_default_command, bool), repr(is_default_command)
        self.id = id
        self.kind = kind
        self.resource_id = resource_id
        self.is_default_command = is_default_command
        self._class_method = class_method
        self._inst_wr = inst_wr  # weak ref to class instance
        self._args = args or ()

    def __repr__( self ):
        return 'BoundCommand(%r/%r -> %r, args=%r)' % (self.id, self.kind, self._inst_wr, self._args)

    def to_data( self ):
        return tCommand(self.id, self.kind, self.resource_id, self.is_default_command)

    def clone( self, args=None ):
        if args is None:
            args = self._args
        else:
            args = self._args + args
        return BoundCommand(self.id, self.kind, self.resource_id, self.is_default_command, self.enabled, self._class_method, self._inst_wr, args)

    def run( self, request, *args, **kw ):
        inst = self._inst_wr()
        if not inst: return  # inst is deleteddeleted
        log.debug('BoundCommand.run: %s, %r/%r, %r, (%s/%s, %s)', self, self.id, self.kind, inst, self._args, args, kw)
        return self._class_method(inst, request, *(self._args + args), **kw)


class UnboundCommand(object):

    def __init__( self, id, kind, module_name, is_default_command, class_method ):
        assert isinstance(id, str), repr(id)
        assert kind is None or isinstance(kind, str), repr(kind)
        assert isinstance(module_name, str), repr(module_name)
        assert isinstance(is_default_command, bool), repr(is_default_command)
        self.id = id
        self.kind = kind
        self._module_name = module_name
        self.is_default_command = is_default_command
        self._class_method = class_method

    def bind( self, inst, kind ):
        if self.kind is not None:
            kind = self.kind
        return BoundCommand(self.id, kind, self._module_name, self.is_default_command, self._class_method, weakref.ref(inst))


# decorator for object methods
class command(object):

    def __init__( self, id, kind=None, is_default_command=False ):
        assert isinstance(id, str), repr(id)
        assert kind is None or isinstance(kind, str), repr(kind)
        assert isinstance(is_default_command, bool), repr(is_default_command)
        self.id = id
        self.kind = kind
        self.is_default_command = is_default_command

    def __call__( self, class_method ):
        module_name = class_method.__module__.split('.')[-1]
        ## print('### command module:', module_name)
        return UnboundCommand(self.id, self.kind, module_name, self.is_default_command, class_method)


class Commander(object):

    def __init__( self, commands_kind ):
        if hasattr(self, '_commands'):  # multiple inheritance hack
            return  # do not populate _commands twice
        self._commands = []  # BoundCommand list
        for name in dir(self):
            attr = getattr(self, name)
            if not isinstance(attr, UnboundCommand): continue
            bound_cmd = attr.bind(self, commands_kind)
            setattr(self, name, bound_cmd)  # set_enabled must change command for this view, not for all of them
            if bound_cmd.kind == commands_kind:
                self._commands.append(bound_cmd)

    def get_command( self, command_id ):
        for command in self.get_commands():
            assert isinstance(command, BoundCommand), repr(command)
            if command.id == command_id:
                return command
        return None

    def get_commands( self ):
        return self._commands
