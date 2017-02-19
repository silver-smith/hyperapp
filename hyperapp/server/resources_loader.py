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

    def load_resources( self, resource_id ):
        return [rec for rec in self._resources
                if rec.id[:len(resource_id)] == resource_id]
        ## dir = self._dir_map.get(resource_id[0])
        ## assert dir, 'Unknown resource type: %r' % resource_id[0]
        ## log.info('loading resources for %r from %r', encode_path(resource_id), dir)
        ## for fpath in glob.glob(os.path.join(dir, '%s.resources.*.yaml' % resource_id[1])):
        ##     locale = fpath.split('.')[-2]
        ##     log.info('  found resources for locale %r' % locale)
        ##     with open(fpath, 'rb') as f:
        ##         localeResources =  packet_coders.decode('yaml', f.read(), tLocaleResources)
        ##         #yield tResources(resource_id, locale, localeResources)

    def _load_iface_resources( self, dir ):
        for rec in self.load_resources_from_dir(dir):
            id = ['interface'] + rec.id[1:]  # skip module name from id
            log.info('    loaded resource %s: %s', encode_path(id), rec.resource)
            self._resources.append(tResourceRec(id, rec.resource))
