

class TypeError(Exception): pass


def join( *args ):
    return '.'.join(args)


class Type(object):

    def validate( self, value ):
        raise NotImplementedError(self.__class__)


class TString(Type):

    def validate( self, path, value ):
        if not isinstance(value, basestring):
            raise TypeError('%s: String is expected: %r' % (path, value))


class TInt(Type):

    def validate( self, path, value ):
        if not isinstance(value, int):
            raise TypeError('%s: Int is expected: %r' % (path, value))


class TPath(Type):

    def validate( self, path, value ):
        if not isinstance(value, dict):
            raise TypeError('%s: Path (dict) is expected: %r' % (path, value))


class Arg(object):

    def __init__( self, name, type ):
        assert isinstance(type, Type), repr(type)
        self.name = name
        self.type = type

    def validate( self, path, value ):
        self.type.validate(path, value)


class Command(object):

    def __init__( self, command_id, args=None ):
        self.command_id = command_id
        self.args = args or []
        self.name2arg = dict((arg.name, arg) for arg in args or [])

    def validate_request( self, path, **kw ):
        for name, value in kw.items():
            arg = self.name2arg.get(name)
            if not arg:
                raise TypeError('%s: Argument %r for command %r is not supported' % (path, name, self.command_id))
            arg.validate(join(path, self.command_id, name), value)


class Interface(object):

    def __init__( self, iface_id, commands ):
        self.iface_id = iface_id
        self.commands = dict((cmd.command_id, cmd) for cmd in commands)

    def validate_command_request( self, command_id, **kw ):
        cmd = self.commands.get(command_id)
        if not cmd:
            raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        cmd.validate_request(self.iface_id, **kw)


iface_registry = {}  # iface id -> Interface


def register_iface( iface ):
    assert isinstance(iface, Interface), repr(iface)
    iface_registry[iface.iface_id] = iface

def resolve_iface( iface_id ):
    return iface_registry[iface_id]
