import logging
from ..common.util import encode_path
from ..common.htypes import tResourceRec
from ..common import resources_loader

log = logging.getLogger(__name__)


class ResourcesLoader(resources_loader.ResourcesLoader):

    def __init__( self, iface_resources_dir, client_modules_resources_dir ):
        resources_loader.ResourcesLoader.__init__(self)
        self._resources = []  # tResourceRec list
        self._load_iface_resources(iface_resources_dir)
        self._load_client_module_resources(client_modules_resources_dir)

    def load_resources( self, resource_id ):
        return [rec for rec in self._resources
                if rec.id[:len(resource_id)] == resource_id]
    def _load_iface_resources( self, dir ):
        for rec in self.load_resources_from_dir(dir):
            id = ['interface'] + rec.id[1:]  # skip module name from id
            log.info('    loaded resource %s: %s', encode_path(id), rec.resource)
            self._resources.append(tResourceRec(id, rec.resource))

    def _load_client_module_resources( self, dir ):
        for rec in self.load_resources_from_dir(dir):
            id = ['client_module'] + rec.id
            log.info('    loaded resource %s: %s', encode_path(id), rec.resource)
            self._resources.append(tResourceRec(id, rec.resource))
