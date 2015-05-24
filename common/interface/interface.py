

class TypeError(Exception): pass


def join( *args ):
    return '.'.join(args)


class Type(object):

    def validate( self, value ):
        raise NotImplementedError(self.__class__)

    def expect( self, path, value, name, expr ):
        if not expr:
            raise TypeError('%s: %s is expected, but got: %r' % (path, name, value))


class TString(Type):

    def validate( self, path, value ):
        self.expect(path, value, 'String', isinstance(value, basestring))


class TInt(Type):

    def validate( self, path, value ):
        self.expect(path, value, 'Int', isinstance(value, int))


class TPath(Type):

    def validate( self, path, value ):
        self.expect(path, value, 'Path (dict)', isinstance(value, dict))


class Field(object):

    def __init__( self, name, type ):
        assert isinstance(type, Type), repr(type)
        self.name = name
        self.type = type

    def validate( self, path, value ):
        self.type.validate(path, value)


class Command(object):

    def __init__( self, command_id, args=None, result=None ):
        self.command_id = command_id
        self.params_fields  = args or []
        self.result_fields = result
        self.name2arg = dict((field.name, field) for field in args or [])
        self.name2result = dict((field.name, field) for field in result or [])

    def validate_request( self, path, rec ):
        self._validate_record('params', self.name2arg, path, rec)

    def validate_result( self, path, rec ):
        self._validate_record('result', self.name2result, path, rec)

    def _validate_record( self, rec_name, name2field, path, rec ):
        rec_path = join(path, self.command_id, rec_name)
        missing = set(name2field.keys())
        for name, value in rec.items():
            field = name2field.get(name)
            if not field:
                raise TypeError('%s: Unexpected %s field %r for command %r' % (path, rec_name, name, self.command_id))
            field.validate(join(rec_path, name), value)
            missing.remove(name)
        if missing:
            raise TypeError('%s: Missing fields: %s' % (rec_path, ', '.join(missing)))


class GetCommand(Command):

    def validate_result( self, path, rec ):
        pass  # todo


class ElementCommand(Command):

    def __init__( self, command_id, args=None, result=None ):
        args = [Field('element_key', TString())] + (args or [])
        Command.__init__(self, command_id, args, result)


class Interface(object):

    basic_commands = [
        GetCommand('get'),
        Command('unsubscribe'),
        ]

    def __init__( self, iface_id, commands=None ):
        self.iface_id = iface_id
        self.commands = dict((cmd.command_id, cmd) for cmd in (commands or []) + self.basic_commands)

    def get_command( self, command_id ):
        return self.commands[command_id]

    def validate_request( self, command_id, args ):
        cmd = self.commands.get(command_id)
        if not cmd:
            raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        cmd.validate_request(self.iface_id, args)

    def validate_result( self, command_id, rec ):
        cmd = self.commands.get(command_id)
        if not cmd:
            raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        cmd.validate_result(self.iface_id, rec)


class ListInterface(Interface):
        
    def __init__( self, iface_id, commands=None, key_type=TString() ):
        Interface.__init__(self, iface_id, (commands or []) + self.get_basic_commands(key_type))

    def get_basic_commands( self, key_type ):
        return [
            Command('get_elements', [Field('count', TInt()),
                                     Field('key', key_type)]),
                                     ]


iface_registry = {}  # iface id -> Interface


def register_iface( iface ):
    assert isinstance(iface, Interface), repr(iface)
    iface_registry[iface.iface_id] = iface

def resolve_iface( iface_id ):
    return iface_registry[iface_id]
