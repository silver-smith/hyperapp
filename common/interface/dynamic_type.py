from . types import Type, TString, Field, TRecord


class TDynamic(Type):

    discriminator_type = TString()

    def __init__( self, base_cls ):
        self.base_cls = base_cls
        self.registry = {}  # discriminator -> child class

    def resolve( self, discriminator ):
        assert discriminator in self.registry, 'Unknown class discriminator: %r' % discriminator
        return self.registry[discriminator]

    def validate( self, path, value ):
        self.expect(path, value, self.base_cls.__name__, isinstance(value, self.base_cls))


@classmethod
def _register( cls, discriminator ):
    assert isinstance(discriminator, basestring), repr(discriminator)
    cls.discriminator = discriminator
    cls.type.registry[discriminator] = cls

@classmethod
def _get_actual_type( cls ):
    return TRecord([
        Field('discriminator', cls.type.discriminator_type),
        ])

# decorator for base classes
def dynamic_type_base( base_cls ):
    base_cls.register = _register
    base_cls.get_actual_type = _get_actual_type
    base_cls.type = TDynamic(base_cls)
    return base_cls
