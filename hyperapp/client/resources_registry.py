import logging
from ..common.htypes import tLocaleResources

log = logging.getLogger(__name__)


class ResourcesRegistry(object):

    def __init__( self ):
        self._registry = {}

    def register( self, id, locale, resources ):
        assert isinstance(resources, tLocaleResources), repr(resources)
        log.debug('Resource registry: registering %r' % id)
        self._registry[(id, locale)] = resources

    def resolve( self, id, locale ):
        return self._registry.get((id, locale))
