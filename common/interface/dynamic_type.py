from . types import Type, TString, Field, TRecord


class TDynamic(Type):

    discriminator_type = TString()

    def __init__( self, base_cls ):
        self.base_cls = base_cls
        self.registry = {}  # discriminator -> child class

    def resolve( self, discriminator ):
        assert discriminator in self.registry, 'Unknown class discriminator: %r' % discriminator
        return self.registry[discriminator].cls

    def validate( self, path, value ):
        self.expect(path, value, self.base_cls.__name__, isinstance(value, self.base_cls))


# optional base class for dynamic classes
class Dynamic(object):

    def __init__( self, discriminator ):
        assert hasattr(self.__class__, 'registry'), 'Use dynamic_type_base decorator for base class'
        assert discriminator in self.registry, 'Unknown/unregistered class: %r' % discriminator
        self.discriminator = discriminator


class ClassRec(object):

    def __init__( self, cls=None, type=None ):
        self.cls = cls  # derived class or None
        self.type = type  # Type instance or None


@classmethod
def _register( cls, discriminator ):
    assert isinstance(discriminator, basestring), repr(discriminator)
    rec = ClassRec()
    if cls is not cls.type.base_cls:  # called on base class?
        cls.discriminator = discriminator
        rec.cls = cls
        rec.type = cls.my_type
    cls.type.registry[discriminator] = rec

@classmethod
def _get_actual_type( cls ):
    return cls.type.registry[cls.discriminator].type

# decorator for base classes
def dynamic_type_base( base_cls ):
    base_cls.register = _register
    base_cls.get_actual_type = _get_actual_type
    base_cls.type = TDynamic(base_cls)
    base_cls.my_type = None
    return base_cls
