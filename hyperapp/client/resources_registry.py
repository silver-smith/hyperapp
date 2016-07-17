from ..common.htypes import tLocaleResources


class ResourcesRegistry(object):

    def __init__( self ):
        self._registry = {}

    def register( self, id, resources ):
        assert isinstance(resources, tLocaleResources), repr(resources)
        self._registry[(id)] = resources

    def resolve( self, id ):
        return self._registry.get((id))
