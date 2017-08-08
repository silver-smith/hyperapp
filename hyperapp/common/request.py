import logging
from .util import is_list_inst
from .htypes import Interface
from .visual_rep import pprint

log = logging.getLogger(__name__)


class Update(object):

    @classmethod
    def from_data(cls, iface_registry, update):
        iface = iface_registry.resolve(update.iface_id)
        diff = update.diff.decode(iface.diff_type)
        return cls(iface, update.path, diff)

    def __init__(self, iface, path, diff):
        assert isinstance(iface, Interface), repr(iface)
        assert is_list_inst(path, str), repr(path)
        assert isinstance(diff, iface.diff_type)
        self.iface = iface
        self.path = path
        self.diff = diff

    def pprint(self):
        log.info('Update: iface=%s, path=%s, diff:', self.iface.iface_id, self.path)
        pprint(self.iface.diff_type, self.diff)
