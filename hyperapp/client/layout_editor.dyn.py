import asyncio
import logging
from collections import namedtuple

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command as object_command
from .layout import InsertVisualItemDiff, RemoveVisualItemDiff, LayoutWatcher
from .command_hub import CommandHub
from .column import Column
from .tree_object import InsertItemDiff, RemoveItemDiff, TreeObject

_log = logging.getLogger(__name__)


class LayoutEditor(TreeObject):

    _CommandRec = namedtuple('_CommandRec', 'command item_path')

    def __init__(self, layout_watcher):
        super().__init__()
        self._path2item_list = {}
        self._item_commands = {}  # id -> _CommandRec
        layout_watcher.subscribe(self)

    async def _async_init(self, layout):
        root = await self.get_root_item(layout)
        self._add_item([], root.to_item(0, 'root'))

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

    async def get_root_item(self, layout):
        return (await layout.visual_item())

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


class GlobalLayoutEditor(LayoutEditor):

    @classmethod
    async def from_state(cls, state, layout_manager, layout_watcher):
        # Postpone async_init because layout_manager does not have root_layout yet if we are first view on startup.
        return cls(layout_watcher, layout_manager)

    def __init__(self, layout_watcher, layout_manager):
        super().__init__(layout_watcher)
        self._layout_manager = layout_manager

    def get_title(self):
        return "Global view layout"

    @property
    def data(self):
        return htypes.layout_editor.view_layout_editor()

    async def fetch_items(self, path):
        if not self._path2item_list:
            # Not yet async-inited.
            await self._async_init(self._layout_manager.root_layout)
        await super().fetch_items(path)


class ObjectLayoutEditor(LayoutEditor):

    @classmethod
    async def from_state(
            cls,
            state,
            ref_registry,
            async_ref_resolver,
            object_registry,
            object_layout_association,
            object_command_layout_association,
            object_layout_resolver,
            ):
        piece = await async_ref_resolver.resolve_ref_to_object(state.piece_ref)
        object = await object_registry.resolve_async(piece)
        layout = await object_layout_resolver.resolve(state.layout_ref, object)
        layout_watcher = LayoutWatcher()  # todo: save object layout on change
        self = cls(
            ref_registry,
            object_layout_association,
            object_command_layout_association,
            layout_watcher,
            state.piece_ref,
            layout,
            object,
            state.category,
            state.command,
            )
        await self._async_init(layout)
        return self

    def __init__(
            self,
            ref_registry,
            object_layout_association,
            object_command_layout_association,
            layout_watcher,
            piece_ref,
            layout,
            object,
            category,
            command,
            ):
        super().__init__(layout_watcher)
        self._ref_registry = ref_registry
        self._object_layout_association = object_layout_association
        self._object_command_layout_association = object_command_layout_association
        self._piece_ref = piece_ref
        self._layout = layout
        self._object = object
        self._target_category = category
        self._target_command = command  # None for non-command layouts

    def get_title(self):
        title = f"Layout for category: {self._target_category}"
        if self._target_command:
            return f"{title}/{self._target_command}"
        else:
            return title

    @property
    def data(self):
        layout_ref = self._ref_registry.register_object(self._layout.data)
        return htypes.layout_editor.object_layout_editor(self._piece_ref, layout_ref, self._target_category, self._target_command)

    def get_command_list(self):
        return [command for command in super().get_command_list()
                if command.id not in {'replace', '_replace_impl'}]

    async def get_root_item(self, layout):
        item = await self._layout.visual_item()
        return item.with_added_commands([
            self._replace_view,
            ])

    def _object_layout_editor(self, layout_ref):
        piece_ref = self._ref_registry.register_object(self._object.data)
        return htypes.layout_editor.object_layout_editor(piece_ref, layout_ref, self._target_category, command=self._target_command)

    @object_command('replace')
    async def _replace_view(self, path):
        chooser = htypes.view_chooser.view_chooser(self._object.category_list)
        chooser_ref = self._ref_registry.register_object(chooser)
        layout_rec_maker_field = htypes.params_editor.field('layout_rec_maker', chooser_ref)
        layout_ref = self._ref_registry.register_object(self._layout.data)
        editor = self._object_layout_editor(layout_ref)
        return htypes.params_editor.params_editor(
            target_piece_ref=self._ref_registry.register_object(editor),
            target_command_id=self._replace_impl.id,
            bound_arguments=[],
            fields=[layout_rec_maker_field],
            )

    @command('_replace_impl')
    async def _replace_impl(self, layout_rec_maker):
        resource_key = self._object.hashable_resource_key
        layout_rec = await layout_rec_maker(self._object)
        layout_ref = self._ref_registry.register_object(layout_rec)
        if self._target_command:
            self._object_command_layout_association[self._target_category, self._target_command] = layout_ref
        else:
            self._object_layout_association[self._target_category] = layout_ref
        return self._object_layout_editor(layout_ref)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.layout_editor.view_layout_editor, GlobalLayoutEditor.from_state, services.layout_manager, services.layout_watcher)
        services.object_registry.register_type(
            htypes.layout_editor.object_layout_editor,
            ObjectLayoutEditor.from_state,
            services.ref_registry,
            services.async_ref_resolver,
            services.object_registry,
            services.object_layout_association,
            services.object_command_layout_association,
            services.object_layout_resolver,
            )

    @command('open_view_layout')
    async def open_view_layout(self):
        return htypes.layout_editor.view_layout_editor()
