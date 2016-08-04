import os.path
import glob
import logging
from ..common.htypes import tLocaleResources, tResources
from ..common.packet_coders import packet_coders

log = logging.getLogger(__name__)


class ResourcesLoader(object):

    def __init__( self, dir_map ):
        self._dir_map = dir_map  # resource prefix -> dir

    def load_resources( self, resource_id ):
        id_list = resource_id.split('.')
        dir = self._dir_map.get(id_list[0])
        assert dir, 'Unknown resource type: %r' % id_list[0]
        log.info('loading resources for %r' % resource_id)
        for fpath in glob.glob(os.path.join(dir, '%s.resources.*.yaml' % id_list[1])):
            locale = fpath.split('.')[-2]
            log.info('  found resources for locale %r' % locale)
            with open(fpath, 'rb') as f:
                localeResources =  packet_coders.decode('yaml', f.read(), tLocaleResources)
                yield tResources(resource_id, locale, localeResources)
