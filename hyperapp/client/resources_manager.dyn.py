import logging
from hyperapp.common.util import encode_path
from hyperapp.common.module import Module
from . import htypes
from .resources_loader import ResourcesLoader

log = logging.getLogger(__name__)


MODULE_NAME = 'resources_manager'


class ResourcesRegistry(object):

    def __init__(self):
        self._registry = {}

    def register(self, resource_list):
        assert isinstance(resource_list, htypes.resource.resource_rec_list), repr(resource_list)
        for rec in resource_list:
            log.debug('    Resource registry: registering %s: %s', encode_path(rec.id), rec.resource)
            self._registry[tuple(rec.id)] = rec.resource

    def resolve(self, id):
        resource = self._registry.get(tuple(id))
        log.debug('    Resource registry: resolved %s -> %s', encode_path(id), resource)
        return resource

    # return all resources with id starting from this
    def resolve_starting_with(self, id):
        id_tuple = tuple(id)
        size = len(id_tuple)

        def resolve():
            for id, resource in self._registry.items():
                if id[:size] == id_tuple:
                    yield htypes.resource.resource_rec(list(id), resource)

        resource_list = list(resolve)
        log.debug('    Resource registry: resolved starting with %s -> %s', encode_path(id), resource_list)
        return resource_list


class ResourcesManager(object):

    def __init__(self, resources_registry, cache_repository, client_modules_resources_dir):
        self._resources_registry = resources_registry
        self._cache_repository = cache_repository
        self._load_client_modules_resources(client_modules_resources_dir)

    def _load_client_modules_resources(self, dir):
        loader = ResourcesLoader()
        for rec in loader.load_localized_resources_from_dir(dir):
            if rec.id[1] == 'error_message':
                id = rec.id[1:]  # they are global; skip module name and interface id
            else:
                id = ['client_module'] + rec.id
            self.register([htypes.resource.resource_rec(id, rec.resource)])

    def register(self, resource_list):
        assert isinstance(resource_list, htypes.resource.resource_rec_list), repr(resource_list)
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
        return htypes.resource.resource


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.resources_registry = resources_registry = ResourcesRegistry()
        services.resources_manager = ResourcesManager(resources_registry, services.cache_repository, services.client_resources_dir)
