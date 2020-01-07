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

    def __init__(self):
        super().__init__(commands_kind='view')

    @abc.abstractmethod
    def get_view_ref(self):
        pass

    @abc.abstractmethod
    async def create_view(self):
        pass

    @abc.abstractmethod
    async def visual_item(self) -> VisualItem:
        pass
