

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
        self.type.validate(join(path, self.name), value)


class Command(object):

    def __init__( self, command_id, params_fields=None, result_fields=None ):
        self.command_id = command_id
        self.params_fields = params_fields or []
        self.result_fields = result_fields or []

    def get_params_fields( self, iface ):
        return self.params_fields

    def get_result_fields( self, iface ):
        return self.result_fields

    def validate_request( self, iface, path, rec ):
        self._validate_record('params', self.get_params_fields(iface), path, rec)

    def validate_result( self, iface, path, rec ):
        self._validate_record('result', self.get_result_fields(iface), path, rec)

    def _validate_record( self, rec_name, fields, path, rec ):
        rec_path = join(path, self.command_id, rec_name)
        unexpected = set(rec.keys())
        for field in fields:
            if field.name not in rec:
                raise TypeError('%s: Missing field: %s' % (rec_path, field.name))
            field.validate(rec_path, rec[field.name])
            unexpected.remove(field.name)
        if unexpected:
            raise TypeError('%s: Unexpected fields: %s' % (rec_path, ', '.join(unexpected)))


class GetCommand(Command):

    def validate_result( self, iface, path, rec ):
        pass  # todo


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
        cmd.validate_request(self, self.iface_id, args)

    def validate_result( self, command_id, rec ):
        cmd = self.commands.get(command_id)
        if not cmd:
            raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        cmd.validate_result(self, self.iface_id, rec)


class ElementCommand(Command):

    def __init__( self, command_id, args=None, result=None ):
        Command.__init__(self, command_id, args, result)

    def get_params_fields( self, iface ):
        assert isinstance(iface, ListInterface), repr(iface)  # ElementCommands can only be used with ListInterface
        fields = Command.get_params_fields(self, iface)
        return [Field('element_key', iface.key_type)] + fields


class ListInterface(Interface):
        
    def __init__( self, iface_id, commands=None, key_type=TString() ):
        Interface.__init__(self, iface_id, (commands or []) + self.get_basic_commands(key_type))
        self.key_type = key_type

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
