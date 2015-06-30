import datetime
from .. util import is_list_inst
from .. request import ColumnType, Diff, Update


class TypeError(Exception): pass


def join_path( *args ):
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

class TColumnType(TPrimitive):
    type_name = 'column_type'
    type = ColumnType


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
            self.type.validate(join_path(path, self.name), value)


class Record(object):
    pass


class TRecord(Type):

    def __init__( self, fields ):
        assert is_list_inst(fields, Field), repr(fields)
        self.fields = fields

    def validate( self, path, rec ):
        print '*** record validate', path, rec
        for field in self.fields:
            if not hasattr(rec, field.name):
                raise TypeError('%s: Missing field: %s' % (path, field.name))
            field.validate(path, getattr(rec, field.name))

    ## def validate_kw( self, path, rec_kw ):
    ##     self.expect(path, rec_kw, 'dict', isinstance(rec_kw, dict))
    ##     unexpected = set(rec_kw.keys())
    ##     for field in self.fields:
    ##         if field.name not in rec_kw:
    ##             raise TypeError('%s: Missing field: %s' % (path, field.name))
    ##         field.validate(path, rec_kw[field.name])
    ##         unexpected.remove(field.name)
    ##     if unexpected:
    ##         raise TypeError('%s: Unexpected fields: %s' % (path, ', '.join_path(unexpected)))

    def instantiate( self, *args, **kw ):
        fields = dict(kw)
        for field, arg in zip(self.fields, args):
            assert field.name not in fields, 'TRecord.instantiate got multiple values for field %r' % field.name
            fields[field.name] = arg
        rec = Record()
        rec.type = self
        unexpected = set(fields.keys())
        for field in self.fields:
            if field.name in fields:
                value = fields[field.name]
                unexpected.remove(field.name)
            else:
                if isinstance(field.type, TOptional):
                    value = None
                else:
                    raise TypeError('Record field is missing: %r' % field.name)
            field.type.validate(join_path('Record', field.name), value)
            setattr(rec, field.name, value)
        assert not unexpected, 'Unexpected record fields: %s' % ', '.join(unexpected)
        return rec
        

class TList(Type):

    def __init__( self, element_type ):
        assert isinstance(element_type, Type), repr(element_type)
        self.element_type = element_type

    def validate( self, path, value ):
        self.expect(path, value, 'list', isinstance(value, list))
        for idx, item in enumerate(value):
            self.element_type.validate(join_path(path, '#%d' % idx), item)


class TIndexedList(TList):
    pass


class TRow(Type):

    def __init__( self, columns ):
        assert is_list_inst(columns, Type), repr(columns)
        self.columns = columns

    def validate( self, path, value ):
        self.expect(path, value, 'list', isinstance(value, list))
        if len(value) != len(self.columns):
            self.failure(path, 'Wrong row length: %d; required length: %d' % (len(value), len(self.columns)))
        for idx, (item, type) in enumerate(zip(value, self.columns)):
            type.validate(join_path(path, '#%d' % idx), item)


class TPath(Type):

    def validate( self, path, value ):
        self.expect(path, value, 'Path (dict)', isinstance(value, dict))


class TUpdate(Type):

    def __init__( self ):
        self.info_type = TRecord([
            Field('iface_id', TString()),
            Field('path', TPath()),
            ])


# base class for server objects
class Object(object):

    def get( self ):
        raise NotImplementedError(self.__class__)


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
        self.expect(path, value, 'Object', isinstance(value, Object))


tCommand = TRecord([
            Field('id', TString()),
            Field('text', TString()),
            Field('desc', TString()),
            Field('shortcut', TOptional(TString())),
            ])

Command = tCommand.instantiate
