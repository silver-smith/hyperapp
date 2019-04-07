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
                other.type == self.type)

    def __hash__(self):
        return hash((self.id, self.type))


class TreeObserver(ObjectObserver):

    def process_fetch_results(self, path, item_list):
        pass

    def process_diff(self, diff):
        pass


class TreeObject(Object, metaclass=abc.ABCMeta):

    # return Column list
    @abc.abstractmethod
    def get_columns(self):
        pass

    @abc.abstractmethod
    async def fetch_items(self, path):
        pass

    def get_item_command_list(self, item_path):
        return self.get_command_list(kinds=['element'])  # by default all items have same commands

    def _distribute_fetch_results(self, path, item_list):
        for observer in self._observers:
            log.debug('  Calling process_fetch_results on %s/%s', id(observer), observer)
            observer.process_fetch_results(path, item_list)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.TreeObject = TreeObject
        services.TreeColumn = Column
