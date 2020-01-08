import abc
import logging
from collections import namedtuple
from dataclasses import dataclass
from typing import List

from hyperapp.client.commander import Commander
from hyperapp.client.module import ClientModule

_log = logging.getLogger(__name__)


VisualItem = namedtuple('Item', 'idx name text children commands', defaults=[None, None])


@dataclass
class RootVisualItem:
    text: str
    children: List[VisualItem] = None

    def to_item(self, idx, name, commands=None):
        return VisualItem(idx, name, self.text, self.children, commands)


class VisualItemDiff:
    pass


@dataclass
class InsertVisualItemDiff(VisualItemDiff):
    path: List[int]
    idx: int
    item: VisualItem


@dataclass
class RemoveVisualItemDiff(VisualItemDiff):
    path: List[int]


class ViewHandler(Commander, metaclass=abc.ABCMeta):

    def __init__(self, path):
        super().__init__(commands_kind='view')
        self._path = path

    @abc.abstractmethod
    def get_view_ref(self):
        pass

    @abc.abstractmethod
    async def create_view(self):
        pass

    @abc.abstractmethod
    async def visual_item(self) -> VisualItem:
        pass

    def get_current_commands(self):
        return self.get_command_list({'view', 'global', 'object', 'element'})

    def collect_view_commands(self):
        return {self._path: self.get_command_list({'view'})}

    def _get_current_commands_with_child(self, child):
        child_commands = child.get_current_commands()
        child_command_ids = set(command.id for command in child_commands)
        # child commands should override and hide same commands from parents
        my_commands = [command for command in ViewHandler.get_current_commands(self)
                       if command.id not in child_command_ids]
        return [*child_commands, *my_commands]

    def _collect_view_commands_with_children(self, child_handler_it):
        children_commands = {
            path: commands
            for handler in child_handler_it
            for path, commands in handler.collect_view_commands().items()
            }
        return {
            **children_commands,
            **ViewHandler.collect_view_commands(self),
            }
