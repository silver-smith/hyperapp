from . types import join_path, Type, TString, Field, TRecord


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
