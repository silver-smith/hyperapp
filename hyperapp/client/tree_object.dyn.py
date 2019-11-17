import abc
import logging
from dataclasses import dataclass

from hyperapp.common.util import single
from hyperapp.common.htypes import Type, tString
from hyperapp.client.object import ObjectObserver, Object
from hyperapp.client.module import ClientModule
from .column import Column

log = logging.getLogger(__name__)


class TreeObserver(ObjectObserver):

    def process_fetch_results(self, path, item_list):
        pass

    def process_diff(self, path, diff):
        pass


class Diff:
    pass


@dataclass
class AppendItemDiff(Diff):
    item: object


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

    def _distribute_diff(self, path, diff):
        for observer in self._observers:
            log.debug('  Calling process_diff for %s on %s/%s: %s', path, id(observer), observer, diff)
            observer.process_diff(path, diff)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.TreeObject = TreeObject
        services.Column = Column
