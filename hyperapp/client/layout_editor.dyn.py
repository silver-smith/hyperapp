import logging
from collections import namedtuple

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .layout import InsertVisualItemDiff, RemoveVisualItemDiff
from .command_hub import CommandHub
from .layout_manager import LayoutWatcher
from .object_layout_root import ObjectLayoutRoot
from .column import Column
from .tree_object import InsertItemDiff, RemoveItemDiff, TreeObject

_log = logging.getLogger(__name__)


async def _open_piece_do_nothing(piece):
    pass


class LayoutEditor(TreeObject):

    _CommandRec = namedtuple('_CommandRec', 'command item_path')

    @classmethod
    async def from_view_state(cls, state, layout_manager, layout_watcher):
        self = cls(layout_watcher, piece_ref=None, category=None)
        await self._async_init(layout_manager.root_layout)
        return self

    @classmethod
    async def from_object_state(cls, state, ref_registry, async_ref_resolver, object_registry, object_layout_association, object_layout_producer):
        piece = await async_ref_resolver.resolve_ref_to_object(state.piece_ref)
        object = await object_registry.resolve_async(piece)
        command_hub = CommandHub()
        layout = await object_layout_producer.produce_layout(object, command_hub, _open_piece_do_nothing)
        layout_watcher = LayoutWatcher()  # todo: save object layout on change
        layout_root = ObjectLayoutRoot(ref_registry, object_layout_association, layout, object)
        command_hub.init_get_commands(layout_root.get_current_commands)
        self = cls(layout_watcher, state.piece_ref, state.category)
        await self._async_init(layout_root)
        return self

    def __init__(self, layout_watcher, piece_ref, category):
        super().__init__()
        self._piece_ref = piece_ref  # None when opened for view (non-object) layout
        self._target_category = category
        self._path2item_list = {}
        self._item_commands = {}  # id -> _CommandRec
        layout_watcher.subscribe(self)

    async def _async_init(self, layout):
        self._layout = layout  # or ObjectLayoutRoot would be garbage-collected, and it's commands gone.
        root = await layout.visual_item()
        self._add_item([], root.to_item(0, 'root'))

    def get_title(self):
        return "Layout"

    @property
    def data(self):
        if self._piece_ref:
            return htypes.layout_editor.object_layout_editor(self._piece_ref, self._target_category)
        else:
            return htypes.layout_editor.view_layout_editor()

    def get_columns(self):
        return [
            Column('name'),
            Column('text'),
            ]

    @property
    def key_attribute(self):
        return 'idx'

    def get_command(self, command_id):
        rec = self._item_commands.get(command_id)
        if rec:
            return rec.command.partial(rec.item_path)
        return super().get_command(command_id)

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

    # from LayoutWatcher
    def process_layout_diffs(self, vdiff_list):
        for vdiff in vdiff_list:
            if isinstance(vdiff, InsertVisualItemDiff):
                self._add_item(vdiff.path, vdiff.item)
                diff = InsertItemDiff(vdiff.idx, vdiff.item)
                self._distribute_diff(vdiff.path, diff)
            elif isinstance(vdiff, RemoveVisualItemDiff):
                # todo: remove item from self._path2item_list
                self._distribute_diff(vdiff.path, RemoveItemDiff())
            else:
                raise RuntimeError(u"Unknown VisualItemDiff class: {vdiff}")

    def _add_item(self, path, item):
        item_list = self._path2item_list.setdefault(tuple(path), [])
        item_list.insert(item.idx, item)
        item_path = (*path, item.idx)
        for command in item.commands or []:
            self._item_commands[command.id] = self._CommandRec(command, item_path)
        for kid in item.children or []:
            self._add_item(item_path, kid)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.layout_editor.view_layout_editor, LayoutEditor.from_view_state, services.layout_manager, services.layout_watcher)
        services.object_registry.register_type(
            htypes.layout_editor.object_layout_editor,
            LayoutEditor.from_object_state,
            services.ref_registry,
            services.async_ref_resolver,
            services.object_registry,
            services.object_layout_association,
            services.object_layout_producer,
            )

    @command('open_view_layout')
    async def open_view_layout(self):
        return htypes.layout_editor.view_layout_editor()
