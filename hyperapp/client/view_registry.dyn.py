import abc
import logging
from collections import namedtuple
from dataclasses import dataclass
from typing import List

from hyperapp.client.commander import Commander
from hyperapp.client.module import ClientModule

from . import htypes
from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver
from .column import Column
from .tree_object import InsertItemDiff, TreeObject

_log = logging.getLogger(__name__)


class NotApplicable(Exception):

    def __init__(self, object):
        super().__init__("This view producer is not applicable for object {}".format(object))


class ViewProducerRegistry:

    def __init__(self):
        self._producer_list = []

    def register_view_producer(self, producer):
        self._producer_list.append(producer)

    async def produce_view(self, piece, object, observer=None):
        for producer in self._producer_list:
            try:
                return (await producer(piece, object, observer))
            except NotApplicable:
                pass
        raise RuntimeError("No view is known to support object {}".format(object))


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
    item: VisualItem


class LayoutViewer(TreeObject):

    @classmethod
    async def from_state(cls, state, view_resolver):
        handler = await view_resolver.resolve(state.root_ref, [0])
        path2item_list = await cls._load_items(handler)
        return cls(handler, path2item_list)

    def __init__(self, handler, path2item_list):
        super().__init__()
        self._handler = handler
        self._path2item_list = path2item_list

    def get_title(self):
        return "Layout"

    def get_columns(self):
        return [
            Column('name'),
            Column('text'),
            ]

    @property
    def key_attribute(self):
        return 'idx'

    def get_item_command_list(self, item_path):
        if not item_path:
            return []
        item_list = self._path2item_list.get(tuple(item_path[:-1]), [])
        try:
            item = next(i for i in item_list if i.idx == item_path[-1])
        except StopIteration:
            return []
        return [command.wrap(self._process_diff) for command in item.commands or []]

    async def fetch_items(self, path):
        path = tuple(path)
        item_list = self._path2item_list.get(path, [])
        for item in item_list:
            p = path + (item.idx,)
            if p not in self._path2item_list:
                self._distribute_fetch_results(p, [])
        self._distribute_fetch_results(path, item_list)

    @staticmethod
    async def _load_items(handler):
        item_dict = {}

        def add_item(path, item):
            item_list = item_dict.setdefault(path, [])
            item_list.append(item)
            for kid in item.children or []:
                add_item((*path, item.idx), kid)

        root = await handler.visual_item()
        add_item((), root.to_item(0, 'root'))
        return item_dict

    async def _process_diff(self, vdiff):
        if isinstance(vdiff, InsertVisualItemDiff):

            def send_item_diffs(path, item):
                diff = InsertItemDiff(path[-1], item)
                self._distribute_diff(path[:-1], diff)
                for kid in item.children or []:
                    send_item_diffs((*path, item.idx), kid)

            send_item_diffs(vdiff.path, vdiff.item)
        else:
            raise RuntimeError(u"Unknown VisualItemDiff class: {vdiff}")


class ViewHandler(Commander, metaclass=abc.ABCMeta):

    def __init__(self):
        super().__init__(commands_kind='view')

    @abc.abstractmethod
    async def create_view(self, command_registry, view_opener=None):
        pass

    @abc.abstractmethod
    async def visual_item(self) -> VisualItem:
        pass


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_producer_registry = ViewProducerRegistry()
        services.view_registry = view_registry = AsyncCapsuleRegistry('view', services.type_resolver)
        services.view_resolver = view_resolver = AsyncCapsuleResolver(services.async_ref_resolver, view_registry)
        services.object_registry.register_type(htypes.layout_viewer.layout_viewer, LayoutViewer.from_state, services.view_resolver)
