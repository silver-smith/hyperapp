import datetime
from .. util import is_list_inst


class TypeError(Exception): pass


def join( *args ):
    return '.'.join(args)


class Type(object):

    def validate( self, path, value ):
        raise NotImplementedError(self.__class__)

    def expect( self, path, value, name, expr ):
        if not expr:
            self.failure(path, '%s is expected, but got: %r' % (name, value))

    def failure( self, path, desc ):
        raise TypeError('%s: %s' % (path, desc))


class TPrimitive(Type):

    def validate( self, path, value ):
        self.expect(path, value, self.type_name, isinstance(value, self.type))


class TString(TPrimitive):
    type_name = 'string'
    type = basestring

class TInt(TPrimitive):
    type_name = 'int'
    type = (int, long)

class TBool(TPrimitive):
    type_name = 'bool'
    type = bool

class TDateTime(TPrimitive):
    type_name = 'datetime'
    type = datetime.datetime


class TPath(Type):

    def validate( self, path, value ):
        self.expect(path, value, 'Path (dict)', isinstance(value, dict))


class TOptional(Type):

    def __init__( self, type ):
        assert isinstance(type, Type), repr(type)
        self.type = type

    def validate( self, path, value ):
        if value is None: return
        self.type.validate(path, value)


class TRecord(Type):

    def __init__( self, fields ):
        assert is_list_inst(fields, Field), repr(fields)
        self.fields = fields

    def validate( self, path, value ):
        self.expect(path, value, 'dict', isinstance(value, dict))
        name2field = dict((field.name, field) for field in self.fields)
        missing = set(name2field.keys())
        for name, item in value.items():
            field = name2field.get(name)
            if not field:
                self.failure(path, 'Unexpected field: %r' % name)
            field.validate(path, item)
            missing.remove(name)
        if missing:
            self.failure(path, 'Missing fields: %s' % ', '.join(missing))


class TList(Type):

    def __init__( self, element_type ):
        assert isinstance(element_type, Type), repr(element_type)
        self.element_type = element_type

    def validate( self, path, value ):
        self.expect(path, value, 'list', isinstance(value, list))
        for idx, item in enumerate(value):
            self.element_type.validate(join(path, '#%d' % idx), item)


class TRow(Type):

    def __init__( self, columns ):
        assert is_list_inst(columns, Type), repr(columns)
        self.columns = columns

    def validate( self, path, value ):
        self.expect(path, value, 'list', isinstance(value, list))
        if len(value) != len(self.columns):
            self.failure(path, 'Wrong row length: %d; required length: %d' % (len(value), len(self.columns)))
        for idx, (item, type) in enumerate(zip(value, self.columns)):
            type.validate(join(path, '#%d' % idx), item)

        
class Field(object):

    def __init__( self, name, type ):
        assert isinstance(name, str), repr(name)
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

    def get_command_params_fields( self, command_id ):
        return self.commands[command_id].get_params_fields(self)

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
        
    def __init__( self, iface_id, columns, commands=None, key_type=TString() ):
        assert is_list_inst(columns, Type), repr(columns)
        self.columns = columns
        self.key_type = key_type
        Interface.__init__(self, iface_id, (commands or []) + self._get_basic_commands(key_type))

    def _get_basic_commands( self, key_type ):
        return [
            Command('get_elements', [Field('count', TInt()),
                                     Field('key', key_type)],
                                    [Field('fetched_elements', self._get_fetched_elements_type())]),
                ]

    def _get_fetched_elements_type( self ):
        return TRecord([
            Field('elements', TList(self._get_element_type())),
            Field('has_more', TBool()),
            ])

    def _get_element_type( self ):
        return TRecord([
            Field('commands', TList(self._get_command_type())),
            Field('key', self.key_type),
            Field('row', TRow(self.columns)),
            ])

    def _get_command_type( self ):
        return TRecord([
            Field('id', TString()),
            Field('text', TString()),
            Field('desc', TString()),
            Field('shortcut', TOptional(TString())),
            ])


iface_registry = {}  # iface id -> Interface


def register_iface( iface ):
    assert isinstance(iface, Interface), repr(iface)
    iface_registry[iface.iface_id] = iface

def resolve_iface( iface_id ):
    return iface_registry[iface_id]
