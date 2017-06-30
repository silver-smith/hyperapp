import logging
from ..common.util import encode_path
from ..common.resources_loader import ResourcesLoader

log = logging.getLogger(__name__)


class ResourcesRegistry(object):

    def __init__(self, resource_types):
        self._resource_types = resource_types
        self._registry = {}

    def register(self, resource_list):
        assert isinstance(resource_list, self._resource_types.resource_rec_list), repr(resource_list)
        for rec in resource_list:
            log.debug('    Resource registry: registering %s: %s', encode_path(rec.id), rec.resource)
            self._registry[tuple(rec.id)] = rec.resource

    def resolve(self, id):
        log.debug('### Resource registry: resolving %s -> %s', encode_path(id), self._registry.get(tuple(id)))
        return self._registry.get(tuple(id))

    # return all resources with id starting from this
    def resolve_starting_with(self, id):
        id_tuple = tuple(id)
        size = len(id_tuple)
        for id, resource in self._registry.items():
            if id[:size] == id_tuple:
                yield self._resource_types.resource_rec(list(id), resource)


class ResourcesManager(object):

    def __init__(self, resource_types, param_editor_types, resources_registry, cache_repository, client_modules_resources_dir):
        self._resource_types = resource_types
        self._param_editor_types = param_editor_types
        self._resources_registry = resources_registry
        self._cache_repository = cache_repository
        self._load_client_modules_resources(client_modules_resources_dir)

    def _load_client_modules_resources(self, dir):
        loader = ResourcesLoader(self._resource_types, self._param_editor_types)
        for rec in loader.load_localized_resources_from_dir(dir):
            if rec.id[1] == 'error_message':
                id = rec.id[1:]  # they are global; skip module name and interface id
            else:
                id = ['client_module'] + rec.id[1:]  # skip module name from id
            self.register([self._resource_types.resource_rec(id, rec.resource)])

    def register(self, resource_list):
        assert isinstance(resource_list, self._resource_types.resource_rec_list), repr(resource_list)
        self._resources_registry.register(resource_list)
        for rec in resource_list:
            self._cache_repository.store_value(self._cache_key(rec.id), rec.resource, self._cache_type())

    def resolve(self, id):
        resource = self._resources_registry.resolve(id)
        if resource is None:
            resource = self._cache_repository.load_value(self._cache_key(id), self._cache_type())
        return resource

    def resolve_starting_with(self, id):
        return self._resources_registry.resolve_starting_with(id)
        # todo: may be load from cache repository also

    def _cache_key(self, id):
        return ['resources'] + id

    def _cache_type(self):
        return self._resource_types.resource
