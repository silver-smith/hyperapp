import datetime
from ..util import is_list_inst


class TypeError(Exception): pass


def join_path( *args ):
    return '.'.join([_f for _f in args if _f])


class LateBindingTypes(object):
    pass

lbtypes = LateBindingTypes()


class Type(object):

    def __call__( self, *args, **kw ):
        return self.instantiate(*args, **kw)

    def __instancecheck__( self, value ):
        raise NotImplementedError(self.__class__)

    def to_data( self ):
        raise NotImplementedError(self.__class__)
        
    def expect( self, path, value, name, expr ):
        if not expr:
            self.failure(path, '%s is expected, but got: %r' % (name, value))

    def assert_( self, path, expr, desc ):
        if not expr:
            self.failure(path, desc)

    def failure( self, path, desc ):
        raise TypeError('%s: %s' % (path, desc))


class TPrimitive(Type):

    type_id = 'primitive'

    @classmethod
    def from_data( cls, registry, rec ):
        return cls()

    def __repr__( self ):
        return 'TPrimitive(%s)' % repr(self.get_type())

    def __eq__( self, other ):
        return isinstance(other, TPrimitive) and other.type_name == self.type_name

    def __instancecheck__( self, value ):
        return isinstance(value, self.get_type())

    def get_type( self ):
        return self.type

    @classmethod
    def register_meta( cls ):
        lbtypes.tPrimitiveMeta = lbtypes.tMetaType.register(cls.type_id, base=lbtypes.tRootMetaType)

    @classmethod
    def register( cls, type_registry ):
        type_registry.register(cls.type_name, cls.from_data)

    def to_data( self ):
        return lbtypes.tPrimitiveMeta(self.type_name)


class TNone(TPrimitive):
    type_name = 'none'
    type = type(None)

class TString(TPrimitive):
    type_name = 'string'
    type = str

class TBinary(TPrimitive):
    type_name = 'binary'
    type = bytes

class TInt(TPrimitive):
    type_name = 'int'
    type = int

class TBool(TPrimitive):
    type_name = 'bool'
    type = bool

class TDateTime(TPrimitive):
    type_name = 'datetime'
    type = datetime.datetime


tNone = TNone()
tString = TString()
tBinary = TBinary()
tInt = TInt()
tBool = TBool()
tDateTime = TDateTime()


class TOptional(Type):

    type_id = 'optional'

    @classmethod
    def from_data( cls, registry, rec ):
        base_t = registry.resolve(rec.base)
        return cls(base_t)

    def __init__( self, base_t ):
        assert isinstance(base_t, Type), repr(base_t)
        self.base_t = base_t

    def __repr__( self ):
        return 'TOptional(%r)' % self.base_t

    def __eq__( self, other ):
        return isinstance(other, TOptional) and other.base_t == self.base_t

    def __instancecheck__( self, value ):
        return value is None or isinstance(value, self.base_t)

    @classmethod
    def register_meta( cls ):
        lbtypes.tOptionalMeta = lbtypes.tMetaType.register(
            cls.type_id, base=lbtypes.tRootMetaType, fields=[Field('base', lbtypes.tMetaType)])

    @classmethod
    def register( cls, type_registry ):
        type_registry.register(cls.type_id, cls.from_data)

    def to_data( self ):
        return lbtypes.tOptionalMeta(self.type_id, self.base_t.to_data())

lbtypes.TOptional = TOptional


class Field(object):

    @classmethod
    def from_data( cls, registry, rec ):
        return cls(rec.name, registry.resolve(rec.type))

    def __init__( self, name, type, default=None ):
        assert isinstance(name, str), repr(name)
        assert isinstance(type, Type), repr(type)
        assert default is None or isinstance(default, type), repr(default)
        self.name = name
        self.type = type
        self.default = default

    @classmethod
    def register_meta( cls ):
        lbtypes.tRecordFieldMeta = TRecord([
            Field('name', tString),
            Field('type', lbtypes.tMetaType),
            ])

    def to_data( self ):
        return lbtypes.tRecordFieldMeta(self.name, self.type.to_data())

    def isinstance( self, value ):
        if not self.type:
            return True  # todo: check why
        return isinstance(value, self.type)

    def __repr__( self ):
        return '%r: %r' % (self.name, self.type)

    def __eq__( self, other ):
        assert isinstance(other, Field), repr(other)
        return other.name == self.name and other.type == self.type


# class for instantiated records
class Record(object):

    def __init__( self, type ):
        assert isinstance(type, TRecord), repr(type)
        self._type = type

    def __repr__( self ):
        return 'Record: %r' % self._type
    

class TRecord(Type):

    type_id = 'record'

    @classmethod
    def from_data( cls, registry, rec ):
        fields = [Field.from_data(registry, field) for field in rec.fields]
        return cls(fields)

    def __init__( self, fields=None, base=None ):
        assert fields is None or is_list_inst(fields, Field), repr(fields)
        assert base is None or isinstance(base, TRecord), repr(base)
        self.fields = fields or []
        if base:
            self.fields = base.get_fields() + self.fields
        self.base = base

    def __repr__( self ):
        return 'TRecord(%d(%s)<-%s)' % (id(self), ', '.join(map(repr, self.get_fields())), self.base)

    def __eq__( self, other ):
        return isinstance(other, TRecord) and other.fields == self.fields

    def __subclasscheck__( self, cls ):
        ## print '__subclasscheck__', self, cls
        if not isinstance(cls, TRecord):
            return False
        if cls is self:
            return True
        return issubclass(cls.base, self)

    def get_fields( self ):
        return self.fields

    def get_static_fields( self ):
        return self.fields

    def get_field( self, name ):
        for field in self.fields:
            if field.name == name:
                return field
        assert False, repr((name, self.fields))  # Unknown field

    def __instancecheck__( self, rec ):
        ## print '__instancecheck__', self, rec
        if not isinstance(rec, Record):
            return False
        return issubclass(rec._type, self)

    @classmethod
    def register_meta( cls ):
        Field.register_meta()
        lbtypes.tRecordMeta = lbtypes.tMetaType.register(
            cls.type_id, base=lbtypes.tRootMetaType, fields=[Field('fields', TList(lbtypes.tRecordFieldMeta))])

    @classmethod
    def register( cls, type_registry ):
        type_registry.register(cls.type_id, cls.from_data)

    def to_data( self ):
        return lbtypes.tRecordMeta(self.type_id, [field.to_data() for field in self.fields])

    def adopt_args( self, args, kw, check_unexpected=True ):
        path = '<Record>'
        tfields = self.get_fields()
        if check_unexpected:
            self.assert_(path, len(args) <= len(tfields),
                         'instantiate takes at most %d argumants (%d given)' % (len(tfields), len(args)))
        fields = dict(kw)
        for field, arg in zip(tfields, args):
            assert field.name not in fields, 'TRecord.instantiate got multiple values for field %r' % field.name
            fields[field.name] = arg
        adopted_args = {}
        unexpected = set(fields.keys())
        ## print '*** adopt_args', fields, self, [field.name for field in tfields]
        for field in tfields:
            if field.name in fields:
                value = fields[field.name]
                unexpected.remove(field.name)
            else:
                if isinstance(field.type, TOptional):
                    value = None
                elif field.default is not None:
                    value = field.default
                else:
                    raise TypeError('Record field is missing: %r' % field.name)
            assert isinstance(value, field.type), 'Field %r is expected to be %r, but is %r' % (field.name, field.type, value)
            adopted_args[field.name] = value
        if check_unexpected:
            self.assert_(path, not unexpected,
                         'Unexpected fields: %s; allowed are: %s'
                         % (', '.join(unexpected), ', '.join(field.name for field in tfields)))
        return adopted_args

    def instantiate_impl( self, rec, *args, **kw ):
        fields = self.adopt_args(args, kw or {})
        ## print '*** instantiate', self, sorted(fields.keys()), sorted(f.name for f in self.fields), fields
        for name, val in fields.items():
            setattr(rec, name, val)

    def instantiate( self, *args, **kw ):
        rec = Record(self)
        self.instantiate_impl(rec, *args, **kw)
        return rec

lbtypes.TRecord = TRecord
        

class TList(Type):

    type_id = 'list'

    @classmethod
    def from_data( cls, registry, rec ):
        element_t = registry.resolve(rec.element)
        return cls(element_t)

    def __init__( self, element_t ):
        assert isinstance(element_t, Type), repr(element_t)
        self.element_t = element_t

    def __repr__( self ):
        return 'TList(%r)' % self.element_t

    def __eq__( self, other ):
        return isinstance(other, TList) and other.element_t == self.element_t

    def __instancecheck__( self, value ):
        return is_list_inst(value, self.element_t)

    @classmethod
    def register_meta( cls ):
        lbtypes.tListMeta = lbtypes.tMetaType.register(
            cls.type_id, base=lbtypes.tRootMetaType, fields=[Field('element', lbtypes.tMetaType)])

    @classmethod
    def register( cls, type_registry ):
        type_registry.register(cls.type_id, cls.from_data)

    def to_data( self ):
        return lbtypes.tListMeta(self.type_id, self.element_t.to_data())

lbtypes.TList = TList


class TIndexedList(TList):
    type_id = 'indexed_list'

lbtypes.TIndexedList = TIndexedList


tRoute = TList(tString)

tServerRoutes = TRecord([
    Field('public_key_der', tBinary),
    Field('routes', TList(tRoute)),
    ])

tIfaceId = tString

tPath = TList(tString)

tUrl = TRecord([
    Field('iface', tIfaceId),
    Field('public_key_der', tBinary),
    Field('path', tPath),
    ])

tUrlWithRoutes = TRecord(base=tUrl, fields=[
    Field('routes', TList(tRoute)),
    ])

tResourceId = TList(tString)

tCommand = TRecord([
    Field('command_id', tString),
    Field('kind', tString),
    Field('resource_id', tResourceId),
    Field('is_default_command', tBool, default=False),
    ])

tCommandResource = TRecord([
    Field('command_id', tString),
    Field('text', tString),
    Field('desc', TOptional(tString)),
    Field('shortcuts', TList(tString), default=[]),
    ])

tLocaleResources = TRecord([
    Field('commands', TList(tCommandResource)),
    ])

tResources = TRecord([
    Field('resource_id', tResourceId),
    Field('locale', tString),
    Field('resources', tLocaleResources),
    ])
