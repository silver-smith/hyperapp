import abc
import asyncio
import logging
import weakref
from collections import namedtuple
from dataclasses import dataclass
from typing import List

from . import htypes
from .view_command import ViewCommander
from .items_view import map_columns_to_view


_log = logging.getLogger(__name__)


@dataclass
class VisualItem:
    name: str
    text: str
    children: List['VisualItem'] = None


class LayoutWatcher:

    def __init__(self):
        self._observers = weakref.WeakSet()

    def subscribe(self, observer):
        self._observers.add(observer)

    def distribute_diffs(self, diff_list):
        _log.info("Distribute layout diffs %s to %s", diff_list, list(self._observers))
        for observer in self._observers:
            observer.process_layout_diffs(diff_list)


class Layout(ViewCommander, metaclass=abc.ABCMeta):

    def __init__(self, path):
        super().__init__()
        self._path = path

    # todo: use abstractproperty
    @property
    def piece(self):
        raise NotImplementedError(self.__class__)

    @abc.abstractmethod
    async def create_view(self):
        pass

    @abc.abstractmethod
    async def visual_item(self) -> VisualItem:
        pass

    def collect_view_commands(self):
        return [(tuple(self._path), command)
                for command in self.get_all_command_list()
                ]

    def make_visual_item(self, text, name=None, children=None, commands=None, current_commands=None, all_commands=None):
        if not name:
            name = self._path[-1]
        if current_commands is None:
            current_commands = commands or []
        if all_commands is None:
            all_commands = commands or []
        return VisualItem(name, text, children or [], current_commands, all_commands)

    def _merge_commands(self, primary_commands, secondary_commands):
        primary_command_ids = set(command.name for command in primary_commands)
        secondary_commands = [command for command in secondary_commands
                              if command.name not in primary_command_ids]
        return [*primary_commands, *secondary_commands]

    def _collect_view_commands_with_children(self, child_layout_it):
        children_commands = [
            (path, command)
            for layout in child_layout_it
            for path, command in layout.collect_view_commands()
            ]
        return [
            *children_commands,
            *Layout.collect_view_commands(self),
            ]


class GlobalLayout(Layout):

    async def get_current_commands(self):
        return self.get_all_command_list()

    async def _get_current_commands_with_child(self, child):
        # child commands should override and hide same commands from parents
        return self._merge_commands(
            await child.get_current_commands(),
            await GlobalLayout.get_current_commands(self),
            )
