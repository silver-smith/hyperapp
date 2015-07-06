from . types import join_path, Type, TString, Field, TRecord


class TDynamicRec(TRecord):

    def resolve( self, rec ):
        raise NotImplementedError(self.__class__)


class TRegistryRec(TDynamicRec):

    def __init__( self, cls=None ):
        fields = [Field('discriminator', TString())]
        TDynamicRec.__init__(self, fields, cls)
        self.registry = {}  # discriminator value -> TRecord

    def register( self, discriminator, trec=None, cls=None, fields=None ):
        assert trec is None or isinstance(trec, TRecord), repr(trec)
        assert discriminator not in self.registry, repr(discriminator)  # Already registered/dup
        ## print '*** register', discriminator, trec, cls, fields
        self.registry[discriminator] = trec or TRecord(fields, cls, base=self)

    def resolve_rec( self, rec ):
        ## for discriminator, t in self.registry.items():
        ##     if t.cls and isinstance(rec, t.cls):
        ##         break
        ## else:
        ##     discriminator = rec.discriminator
        return self.resolve(rec.discriminator)

    def resolve( self, discriminator ):
        assert discriminator in self.registry, \
               'Dynamic type: unknown discriminator: %r. Known are: %r' \
               % (discriminator, sorted(self.registry.keys()))
        return self.registry[discriminator]


# base class for dynamic classes
class Dynamic(object):

    def __init__( self, discriminator ):
        self.discriminator = discriminator
