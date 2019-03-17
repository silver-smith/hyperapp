import logging
import abc

from hyperapp.common.htypes import Type, tString
from hyperapp.client.object import ObjectObserver, Object
from hyperapp.client.module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'tree_object'


class Column(object):

    def __init__(self, id, type=tString):
        assert isinstance(id, str), repr(id)
        assert isinstance(type, Type), repr(type)
        self.id = id
        self.type = type

    def __eq__(self, other):
        assert isinstance(other, Column), repr(other)
        return (other.id == self.id and
                other.type == self.type and
                other.is_key == self.is_key)

    def __hash__(self):
        return hash((self.id, self.type, self.is_key))


class TreeObserver(ObjectObserver):

    def process_fetch_results(self, path, node_list):
        pass

    def diff_applied(self, diff):
        pass


class TreeObject(Object, metaclass=abc.ABCMeta):

    # return Column list
    @abc.abstractmethod
    def get_columns(self):
        pass

    @abc.abstractmethod
    async def fetch_items(self, path):
        pass

    def _notify_fetch_results(self, path, item_list):
        for observer in self._observers:
            log.debug('  Calling process_fetch_result on %s/%s', id(observer), observer)
            observer.process_fetch_results(path, item_list)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.TreeObject = TreeObject
        services.TreeColumn = Column
