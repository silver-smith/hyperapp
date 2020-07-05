import logging
import sys
import weakref

from ..common.htypes import resource_key_t
from .commander import resource_key_of_class_method, BoundCommand, UnboundCommand

log = logging.getLogger(__name__)


# decorator for view methods
class command(object):

    def __init__(self, id, kind=None, enabled=True):
        assert isinstance(id, str), repr(id)
        assert kind is None or isinstance(kind, str), repr(kind)
        assert isinstance(enabled, bool), repr(enabled)
        self.id = id
        self.kind = kind
        self.enabled = enabled

    def __call__(self, class_method):
        resource_key = resource_key_of_class_method(class_method, 'command', self.id)
        return UnboundViewCommand(self.id, self.kind, resource_key, self.enabled, class_method)


class UnboundViewCommand(UnboundCommand):

    def __init__(self, id, kind, resource_key, enabled, class_method):
        self.id = id
        self.kind = kind
        self._resource_key = resource_key
        self.enabled = enabled
        self._class_method = class_method

    def bind(self, inst, kind):
        if self.kind is not None:
            kind = self.kind
        inst_wr = weakref.ref(inst)
        return BoundCommand(self.id, kind, self._resource_key, self.enabled, self._class_method, inst_wr)


