from collections import namedtuple
import logging
import inspect

log = logging.getLogger(__name__)


class Registry(object):

    _Rec = namedtuple('_Rec', 'factory args kw')

    def __init__(self):
        self._registry = {}  # id -> _Rec

    def id_to_str(self, id):
        return repr(id)

    def register(self, id, factory, *args, **kw):
        log.info('%s: registering %s -> %s(*%r, **%r)',
                     self.__class__.__name__, self.id_to_str(id), factory, args, kw)
        assert id not in self._registry, repr(id)  # Duplicate id
        self._registry[id] = self._Rec(factory, args, kw)

    def is_registered(self, id):
        return id in self._registry

    def _resolve(self, id):
        try:
            return self._registry[id]
        except KeyError:
            raise RuntimeError('Unknown id: %s' % self.id_to_str(id))
