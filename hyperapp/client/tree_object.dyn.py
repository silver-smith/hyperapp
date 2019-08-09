import logging
import abc

from hyperapp.common.util import single
from hyperapp.common.htypes import Type, tString
from hyperapp.client.object import ObjectObserver, Object
from hyperapp.client.module import ClientModule
from .column import Column

log = logging.getLogger(__name__)


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

    @property
    def key_attribute(self):
        return single(column.id for column in self.get_columns() if column.is_key)

    @abc.abstractmethod
    async def fetch_items(self, path):
        pass

    def get_item_command_list(self, item_path):
        return self.get_command_list(kinds=['element'])  # by default all items have same commands

    def _distribute_fetch_results(self, path, item_list):
        for observer in self._observers:
            log.debug('  Calling process_fetch_results for %s on %s/%s: %s', path, id(observer), observer, item_list)
            observer.process_fetch_results(path, item_list)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.TreeObject = TreeObject
        services.Column = Column
