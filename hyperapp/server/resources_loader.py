import os.path
import glob
import logging
from ..common.htypes import tLocaleResources, tResources
from ..common.packet_coders import packet_coders

log = logging.getLogger(__name__)


class ResourcesLoader(object):

    def __init__( self, dir ):
        self._dir = dir

    def load_resources( self, resource_id ):
        log.info('loading resources for %r' % resource_id)
        for fpath in glob.glob(os.path.join(self._dir, '%s.resources.*.yaml' % resource_id)):
            locale = fpath.split('.')[-2]
            log.info('  found resources for locale %r' % locale)
            with open(fpath, 'rb') as f:
                localeResources =  packet_coders.decode('yaml', f.read(), tLocaleResources)
                yield tResources(resource_id, locale, localeResources)
