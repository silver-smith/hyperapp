import logging

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .view_handler import InsertVisualItemDiff, RemoveVisualItemDiff
from .column import Column
from .tree_object import InsertItemDiff, RemoveItemDiff, TreeObject

_log = logging.getLogger(__name__)


class LayoutEditor(TreeObject):

    @classmethod
    async def from_state(cls, state, layout_manager):
        self = cls()
        await self._async_init(layout_manager.root_handler)
        return self

    def __init__(self):
        super().__init__()

    async def _async_init(self, handler):
        item_dict = {}

        def add_item(path, item):
            item_list = item_dict.setdefault(path, [])
            item_list.append(item)
            for kid in item.children or []:
                add_item((*path, item.idx), kid)

        root = await handler.visual_item()
        add_item((), root.to_item(0, 'root'))
        self._path2item_list = item_dict

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
        try:
            item = self._find_item(item_path)
        except KeyError:
            return []
        return item.commands or []

    def _find_item(self, item_path):
        if not item_path:
            raise KeyError(f"Empty item path {item_path}")
        item_list = self._path2item_list.get(tuple(item_path[:-1]), [])
        try:
            return next(i for i in item_list if i.idx == item_path[-1])
        except StopIteration:
            raise KeyError(f"Item is missing at path {item_path}")

    async def fetch_items(self, path):
        path = tuple(path)
        item_list = self._path2item_list.get(path, [])
        for item in item_list:
            p = path + (item.idx,)
            if p not in self._path2item_list:
                self._distribute_fetch_results(p, [])
        self._distribute_fetch_results(path, item_list)

    async def _process_diff_list(self, vdiff_list):
        for vdiff in vdiff_list:
            if isinstance(vdiff, InsertVisualItemDiff):

                def add_item(path, item):
                    item_list = self._path2item_list.setdefault(tuple(path[:-1]), [])
                    item_list.insert(path[-1], item)
                    for kid in item.children or []:
                        add_item((*path, item.idx), kid)

                add_item(vdiff.path, vdiff.item)
                diff = InsertItemDiff(vdiff.idx, vdiff.item)
                self._distribute_diff(vdiff.path, diff)
            elif isinstance(vdiff, RemoveVisualItemDiff):
                self._distribute_diff(vdiff.path, RemoveItemDiff())
            else:
                raise RuntimeError(u"Unknown VisualItemDiff class: {vdiff}")


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(htypes.layout_editor.layout_editor, LayoutEditor.from_state, services.layout_manager)

    @command('open_layout')
    async def open_layout(self):
        return htypes.layout_editor.layout_editor()
