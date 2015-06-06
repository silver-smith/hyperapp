import datetime
from .. util import is_list_inst


class TypeError(Exception): pass


def join( *args ):
    return '.'.join(filter(None, args))


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


class TOptional(Type):

    def __init__( self, type ):
        assert isinstance(type, Type), repr(type)
        self.type = type

    def validate( self, path, value ):
        if value is None: return
        self.type.validate(path, value)

        
class Field(object):

    def __init__( self, name, type ):
        assert isinstance(name, str), repr(name)
        assert type is None or isinstance(type, Type), repr(type)
        self.name = name
        self.type = type

    def validate( self, path, value ):
        if self.type:
            self.type.validate(join(path, self.name), value)


class Record(object): pass


class TRecord(Type):

    def __init__( self, fields ):
        assert is_list_inst(fields, Field), repr(fields)
        self.fields = fields

    def validate( self, path, rec ):
        self.expect(path, rec, 'dict', isinstance(rec, dict))
        unexpected = set(rec.keys())
        for field in self.fields:
            if field.name not in rec:
                raise TypeError('%s: Missing field: %s' % (path, field.name))
            field.validate(path, rec[field.name])
            unexpected.remove(field.name)
        if unexpected:
            raise TypeError('%s: Unexpected fields: %s' % (path, ', '.join(unexpected)))


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


class TPath(Type):

    def validate( self, path, value ):
        self.expect(path, value, 'Path (dict)', isinstance(value, dict))


class TObject(TRecord):

    def __init__( self ):
        TRecord.__init__(self, [
            Field('iface_id', TString()),
            Field('path', TPath()),
            Field('proxy_id', TString()),
            Field('view_id', TString()),
            Field('contents', None),
            ])

    def validate( self, path, value ):
        if value is None: return  # missing objects are allowed
        TRecord.validate(self, path, value)
        iface_id = value['iface_id']
        iface = resolve_iface(iface_id)
        assert iface, repr(iface_id)  # Unknown iface
        iface.validate_contents(join(path, 'contents'), value['contents'])


class Command(object):

    def __init__( self, command_id, params_fields=None, result_fields=None ):
        self.command_id = command_id
        self.params_fields = params_fields or []
        self.result_fields = result_fields or []

    def get_params_type( self, iface ):
        return TRecord(self.get_params_fields(iface))

    def get_result_type( self, iface ):
        return TRecord(self.get_result_fields(iface))

    def get_params_fields( self, iface ):
        return self.params_fields

    def get_result_fields( self, iface ):
        return self.result_fields

    def validate_request( self, iface, path, params_dict ):
        self._validate_record('params', self.get_params_type(iface), path, params_dict)

    def validate_result( self, iface, path, result_dict ):
        self._validate_record('result', self.get_result_type(iface), path, result_dict)

    def _validate_record( self, rec_name, type, path, rec_dict ):
        rec_path = join(path, self.command_id, rec_name)
        type.validate(rec_path, rec_dict)


class OpenCommand(Command):

    def get_result_type( self, iface ):
        return TObject()


class SubscribeCommand(Command):

    def __init__( self ):
        Command.__init__(self, 'subscribe')

    def get_result_type( self, iface ):
        return iface.get_contents_type()


class Interface(object):

    basic_commands = [
        OpenCommand('get'),
        SubscribeCommand(),
        Command('unsubscribe'),
        ]

    def __init__( self, iface_id, content_fields=None, commands=None ):
        assert is_list_inst(content_fields or [], Field), repr(content_fields)
        assert is_list_inst(commands or [], Command), repr(commands)
        self.iface_id = iface_id
        self.content_fields = content_fields or []
        self.commands = dict((cmd.command_id, cmd) for cmd in (commands or []) + self.basic_commands)

    def is_open_command( self, command_id ):
        return isinstance(self.commands[command_id], OpenCommand)

    def get_command_params_type( self, command_id ):
        return self.commands[command_id].get_params_type(self)

    def get_command_result_type( self, command_id ):
        return self.commands[command_id].get_result_type(self)

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

    def validate_contents( self, path, value ):
        self.get_contents_type().validate(path, value)

    def get_contents_type( self ):
        return TRecord(self.get_default_content_fields() + self.content_fields)

    def get_default_content_fields( self ):
        return [Field('commands', TList(self._get_command_type()))]

    def _get_command_type( self ):
        return TRecord([
            Field('id', TString()),
            Field('text', TString()),
            Field('desc', TString()),
            Field('shortcut', TOptional(TString())),
            ])


class ElementCommand(Command):

    def get_params_fields( self, iface ):
        assert isinstance(iface, ListInterface), repr(iface)  # ElementCommands can only be used with ListInterface
        fields = Command.get_params_fields(self, iface)
        return [Field('element_key', iface.key_type)] + fields


class ElementOpenCommand(ElementCommand, OpenCommand):

    get_params_fields = ElementCommand.get_params_fields
    get_result_type = OpenCommand.get_result_type


class ListInterface(Interface):
        
    def __init__( self, iface_id, content_fields=None, columns=None, commands=None, key_type=TString() ):
        assert is_list_inst(columns, Type), repr(columns)
        self.columns = columns
        self.key_type = key_type
        Interface.__init__(self, iface_id, content_fields, (commands or []) + self._get_basic_commands(key_type))

    def get_default_content_fields( self ):
        return Interface.get_default_content_fields(self) + [
            Field('columns', TList(self._get_column_type())),
            Field('elements', TList(self._get_element_type())),
            Field('has_more', TBool()),
            Field('selected_key', TOptional(self.key_type)),
            ]

    def _get_column_type( self ):
        return TRecord([
            Field('id', TString()),
            Field('type', TString()),
            Field('title', TOptional(TString())),
            ])

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


class IfaceRegistry(object):

    def __init__( self ):
        self.registry = {}  # iface id -> Interface

    def register( self, iface ):
        assert isinstance(iface, Interface), repr(iface)
        self.registry[iface.iface_id] = iface

    def resolve( self, iface_id ):
        return self.registry[iface_id]


iface_registry = IfaceRegistry()

def register_iface( iface ):
    iface_registry.register(iface)

def resolve_iface( iface_id ):
    return iface_registry.resolve(iface_id)
