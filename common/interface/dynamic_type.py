from . types import join_path, Type, TString, Field, TRecord


class TDynamic(Type):

    # fixed_fields = []

    def get_fixed_fields( self ):
        return self.fixed_fields

    def get_dynamic_fields( self, fixed_rec ):
        raise NotImplementedError(self.__class__)

    def get_class( self, fixed_rec ):
        raise NotImplementedError(self.__class__)

    def instantiate_fixed( self, **fields ):
        t = TRecord(self.get_fixed_fields())
        return t.instantiate(**fields)

    def instantiate( self, **fields ):
        ft = TRecord(self.get_fixed_fields())
        fixed_rec = ft.instantiate_impl(kw=fields, check_unexpected=False)
        t = TRecord(self.get_fixed_fields() + self.get_dynamic_fields(fixed_rec))
        t.use_class(self.get_class(fixed_rec))
        return t.instantiate(**fields)


class RegistryRec(object):

    def __init__( self, cls=None, dynamic_fields=None ):
        assert dynamic_fields is None or is_list_inst(dynamic_fields, Field), repr(dynamic_fields)
        self.cls = cls  # derived class or None
        self.dynamic_fields = dynamic_fields  # Field list


class TDynamicRegistry(Type):

    fixed_fields = [
        Field('discriminator', TString()),
        ]

    def __init__( self ):
        self.registry = {}  # discriminator value -> RegistryRec

    def register( self, discriminator, fields=None, cls=None ):
        reg_rec = self.registry.get(discriminator)
        if fields:
            assert not reg_rec, 'Discriminator is already registered: %r' % discriminator
            self.registry[discriminator] = RegistryRec(cls, fields)
            
        else:
            assert reg_rec, 'Discriminator is unknown: %r' % discriminator
            assert reg_rec.cls is None or issubclass(cls, reg_rec.cls), \
                   repr(reg_rec.cls)  # must be subclass to override
            reg_rec.cls = cls

    def get_dynamic_fields( self, fixed_rec ):
        reg_rec = self._resolve(fixed_rec)
        return reg_rec.dynamic_fields

    def get_class( self, fixed_rec ):
        reg_rec = self._resolve(fixed_rec)
        return reg_rec.cls

    def _resolve( self, fixed_rec ):
        assert fixed_rec.discriminator in self.registry, \
               'Dynamic type: unknown discriminator: %r. Known are: %r' \
               % (fixed_rec.discriminator, sorted(self.registry.keys()))
        return self.registry[fixed_rec.discriminator]


class TDynamic(Type):

    discriminator_type = TString()

    def __init__( self, base_cls ):
        self.base_cls = base_cls
        self.registry = {}  # discriminator -> child class

    def resolve( self, discriminator ):
        assert discriminator in self.registry, 'Unknown class discriminator: %r' % discriminator
        rec = self.registry[discriminator]
        return (rec.actual_type, rec.cls if rec.cls else self.base_cls)

    def validate( self, path, value ):
        self.expect(path, value, self.base_cls.__name__, isinstance(value, self.base_cls))
        self.assert_(path, value.__class__ is not self.base_cls, 'Expected derived from %r' % self.base_cls.__name__)
        t = value.get_actual_type()
        if t:
            t.validate(join_path(path, value.discriminator), value)


# optional base class for dynamic classes
class Dynamic(object):

    def __init__( self, discriminator ):
        assert hasattr(self.__class__, 'dyn_type'), 'Use dynamic_type_base decorator for base class'
        assert discriminator in self.dyn_type.registry, 'Unknown/unregistered class: %r' % discriminator
        self.discriminator = discriminator


class ClassRec(object):

    def __init__( self, cls=None, actual_type=None ):
        self.cls = cls  # derived class or None
        self.actual_type = actual_type  # Type instance or None


@classmethod
def _register( self_cls, discriminator, cls=None ):
    assert isinstance(discriminator, basestring), repr(discriminator)
    registry = self_cls.dyn_type.registry
    if discriminator in registry:
        assert cls or self_cls is not self_cls.dyn_type.base_cls  # overriding used for setting custom class only
        registry[discriminator].cls = cls or self_cls
        return
    rec = ClassRec()
    if self_cls is self_cls.dyn_type.base_cls:  # called on base class?
        rec.cls = cls
    else:
        self_cls.discriminator = discriminator
        rec.cls = cls or self_cls
        rec.actual_type = self_cls.actual_type
    registry[discriminator] = rec

def _get_actual_type( self ):
    return self.dyn_type.registry[self.discriminator].actual_type

# decorator for base classes
def dynamic_type_base( base_cls ):
    base_cls.register = _register
    base_cls.get_actual_type = _get_actual_type
    base_cls.dyn_type = TDynamic(base_cls)
    base_cls.actual_type = None
    return base_cls
