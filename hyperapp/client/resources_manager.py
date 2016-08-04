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


class ResourcesManager(object):

    def __init__( self, resources_registry, cache_repository ):
        self._resources_registry = resources_registry
        self._cache_repository = cache_repository

    def register( self, id, locale, resources ):
        assert isinstance(resources, tLocaleResources), repr(resources)
        self._resources_registry.register(id, locale, resources)
        self._cache_repository.store_value(self._cache_key(id, locale), resources, self._cache_type())

    def resolve( self, id, locale ):
        resources = self._resources_registry.resolve(id, locale)
        if resources is None:
            resources = self._cache_repository.load_value(self._cache_key(id, locale), self._cache_type())
        return resources

    def _cache_key( self, id, locale ):
        return ['resources', id, locale]

    def _cache_type( self ):
        return tLocaleResources
