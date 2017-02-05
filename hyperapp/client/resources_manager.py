import logging
from ..common.util import is_list_inst
from ..common.htypes import tResource, tResourceList

log = logging.getLogger(__name__)


class ResourcesRegistry(object):

    def __init__( self ):
        self._registry = {}

    def register( self, resource_list ):
        assert isinstance(resource_list, tResourceList), repr(resource_list)
        for rec in resource_list:
            log.debug('Resource registry: registering %r', rec.id)
            self._registry[tuple(rec.id)] = rec.resource

    def resolve( self, id ):
        return self._registry.get(tuple(id))


class ResourcesManager(object):

    def __init__( self, resources_registry, cache_repository ):
        self._resources_registry = resources_registry
        self._cache_repository = cache_repository

    def register( self, resource_list ):
        assert is_list_inst(resource_list, tResourceList), repr(resource_list)
        self._resources_registry.register(resource_list)
        for rec in resource_list:
            self._cache_repository.store_value(self._cache_key(rec.id), rec.resource, self._cache_type())

    def resolve( self, id ):
        resource = self._resources_registry.resolve(id)
        if resource is None:
            resource = self._cache_repository.load_value(self._cache_key(id), self._cache_type())
        return resource

    def _cache_key( self, id ):
        return ['resources'] + id

    def _cache_type( self ):
        return tResource
