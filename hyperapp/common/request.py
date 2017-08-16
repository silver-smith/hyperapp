import logging
from .util import is_list_inst
from .htypes import Interface, ListInterface
from .diff import Diff, SimpleDiff
from .list_object import ListDiff
from .visual_rep import pprint

log = logging.getLogger(__name__)


class Update(object):

    @classmethod
    def from_data(cls, iface_registry, update):
        iface = iface_registry.resolve(update.iface)
        diff = update.diff.decode(iface.diff_type)
        if isinstance(iface, ListInterface):
            diff = ListDiff.from_data(iface, diff)
        return cls(iface, update.path, diff)

    def __init__(self, iface, path, diff):
        assert isinstance(iface, Interface), repr(iface)
        assert is_list_inst(path, str), repr(path)
        assert isinstance(diff, Diff), repr(diff)
        diff.to_data(iface)  # check diff attributes types
        self.iface = iface
        self.path = path
        self.diff = diff

    def pprint(self):
        log.info('Update: iface=%s, path=%s, diff:', self.iface.iface_id, self.path)
        pprint(self.iface.diff_type, self.diff.to_data(self.iface))
