import asyncio
import logging
from collections import namedtuple

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command as object_command
from .layout_handle import InsertVisualItemDiff, RemoveVisualItemDiff, UpdateVisualItemDiff, LayoutWatcher
from .command_hub import CommandHub
from .column import Column
from .tree_object import InsertItemDiff, RemoveItemDiff, UpdateItemDiff, TreeObject

_log = logging.getLogger(__name__)


class LayoutEditor(TreeObject):

    _CommandRec = namedtuple('_CommandRec', 'command item_path')

    def __init__(self, layout_watcher):
        super().__init__()
        self._path2item_list = {}
        self._current_item_commands = {}  # id -> _CommandRec
        self._all_item_commands = {}  # id -> _CommandRec
        layout_watcher.subscribe(self)

    async def _async_init(self, layout):
        root = await self.get_root_item(layout)
        self._append_item([], root)

    @property
    def type(self):
        return htypes.layout_editor.layout_editor_object_type(
            command_list=tuple(
                htypes.object_type.object_command(command.command.id, result_object_type_ref=None)
                for command in self._all_item_commands.values()
                ),
            )

    @property
    def columns(self):
        return [
            Column('name', is_key=True),
            Column('text'),
            ]

    def get_command(self, command_id):
        rec = self._all_item_commands.get(command_id)
        if rec:
            return rec.command.partial(rec.item_path)
        return super().get_command(command_id)

    def get_all_command_list(self):
        return [rec.command for rec in self._all_item_commands.values()]

    def get_item_command_list(self, item_path):
        try:
            item = self._find_item(item_path)
        except KeyError:
            return []
        return item.current_commands or []

    def _find_item(self, item_path):
        if not item_path:
            raise KeyError(f"Empty item path {item_path}")
        item_list = self._path2item_list.get(tuple(item_path[:-1]), [])
        try:
            return next(i for i in item_list if i.name == item_path[-1])
        except StopIteration:
            raise KeyError(f"Item is missing at path {item_path}")

    async def fetch_items(self, path):
        path = tuple(path)
        item_list = self._path2item_list.get(path, [])
        for item in item_list:
            p = (*path, item.name)
            if p not in self._path2item_list:
                self._distribute_fetch_results(p, [])
        self._distribute_fetch_results(path, item_list)

    async def get_root_item(self, layout):
        return (await layout.visual_item())

    # from LayoutWatcher
    def process_layout_diffs(self, vdiff_list):
        for vdiff in vdiff_list:
            if isinstance(vdiff, InsertVisualItemDiff):
                self._insert_item(vdiff.idx, vdiff.path, vdiff.item)
                diff = InsertItemDiff(vdiff.idx, vdiff.item)
                self._distribute_diff(vdiff.path, diff)
            elif isinstance(vdiff, RemoveVisualItemDiff):
                # todo: remove item from self._path2item_list
                self._distribute_diff(vdiff.path, RemoveItemDiff())
            elif isinstance(vdiff, UpdateVisualItemDiff):
                parent_path = tuple(vdiff.path[:-1])
                item_list = self._path2item_list[parent_path]
                item_idx = self._item_idx_by_name(item_list, vdiff.path[-1])
                item_list[item_idx] = vdiff.item
                diff = UpdateItemDiff(vdiff.item)
                self._distribute_diff(vdiff.path, diff)
            else:
                raise RuntimeError(u"Unknown VisualItemDiff class: {vdiff}")

    @staticmethod
    def _item_idx_by_name(item_list, name):
        for idx, item in enumerate(item_list):
            if item.name == name:
                return idx
        raise RuntimeError(f"Invalid visual item update: no item with name {name!r} among {item_list}")

    def _insert_item(self, idx, path, item):
        item_list = self._path2item_list.setdefault(tuple(path), [])
        item_list.insert(idx, item)
        self._add_item_commands_and_children(path, item)

    def _append_item(self, path, item):
        item_list = self._path2item_list.setdefault(tuple(path), [])
        item_list.append(item)
        self._add_item_commands_and_children(path, item)

    def _add_item_commands_and_children(self, path, item):
        item_path = (*path, item.name)
        for command in item.all_commands:
            self._all_item_commands[command.id] = self._CommandRec(command, item_path)
        for kid in item.children:
            self._append_item(item_path, kid)


class GlobalLayoutEditor(LayoutEditor):

    @classmethod
    async def from_state(cls, state, layout_manager, layout_watcher):
        # Postpone async_init because layout_manager does not have root_layout yet if we are first view on startup.
        return cls(layout_watcher, layout_manager)

    def __init__(self, layout_watcher, layout_manager):
        super().__init__(layout_watcher)
        self._layout_manager = layout_manager

    @property
    def title(self):
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
            cls, state,
            mosaic, async_ref_resolver, object_registry, object_layout_registry, object_layout_association, create_layout_handle):
        object_type = await async_ref_resolver.summon(state.object_type_ref)
        origin_object_type = await async_ref_resolver.summon_opt(state.origin_object_type_ref)
        handle = await create_layout_handle(object_type, origin_object_type, state.origin_command_id)
        self = cls(mosaic, object_layout_registry, object_layout_association, object_type, origin_object_type, state.origin_command_id, handle)
        await self._async_init(handle.layout)
        return self

    def __init__(self,
                 mosaic, object_layout_registry, object_layout_association,
                 object_type, origin_object_type, origin_command_id, layout_handle):
        super().__init__(layout_handle.watcher)
        self._mosaic = mosaic
        self._object_layout_registry = object_layout_registry
        self._object_layout_association = object_layout_association
        self._object_type = object_type
        self._origin_object_type = origin_object_type
        self._origin_command_id = origin_command_id
        self._layout_handle = layout_handle

    @property
    def title(self):
        if self._origin_object_type:
            return f"Edit layout for: {self._origin_object_type._t.name}/{self._origin_command_id}"
        else:
            return f"Edit layout for type: {self._object_type._t.name}"

    @property
    def data(self):
        object_type_ref = self._mosaic.put(self._object_type)
        origin_object_type_ref = self._mosaic.put_opt(self._origin_object_type)
        return htypes.layout_editor.object_layout_editor(object_type_ref, origin_object_type_ref, self._origin_command_id)

    def get_command_list(self):
        return [command for command in super().get_command_list()
                if command.id not in {'replace', '_replace_impl'}]

    async def get_root_item(self, layout):
        item = await self._layout_handle.layout.visual_item()
        return item.with_added_commands([
            self._replace_view,
            ])

    def process_layout_diffs(self, vdiff_list):
        super().process_layout_diffs(vdiff_list)
        layout = self._layout_handle.layout
        if self._origin_object_type:
            self._object_layout_association.associate_command(self._origin_object_type, self._origin_command_id, layout)
        else:
            self._object_layout_association.associate_type(self._object_type, layout)

    @object_command('replace', kind='element')
    async def _replace_view(self, path):
        object_type_ref = self._mosaic.put(self._object_type)
        chooser = htypes.view_chooser.view_chooser(object_type_ref)
        chooser_ref = self._mosaic.put(chooser)
        layout_data_maker_field = htypes.params_editor.field('layout_data_maker', chooser_ref)
        return htypes.params_editor.params_editor(
            target_piece_ref=self._mosaic.put(self.data),
            target_command_id=self._replace_impl.id,
            bound_arguments=[],
            fields=[layout_data_maker_field],
            )

    @command('_replace_impl')
    async def _replace_impl(self, layout_data_maker):
        layout_data = await layout_data_maker(self._object_type)
        layout = await self._object_layout_registry.animate(layout_data, ['root'], self._layout_handle.watcher)
        await self._layout_handle.set_layout(layout)
        return self.data


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        services.object_registry.register_actor(
            htypes.layout_editor.view_layout_editor, GlobalLayoutEditor.from_state, services.layout_manager, services.layout_watcher)
        services.object_registry.register_actor(
            htypes.layout_editor.object_layout_editor,
            ObjectLayoutEditor.from_state,
            services.mosaic,
            services.async_ref_resolver,
            services.object_registry,
            services.object_layout_registry,
            services.object_layout_association,
            services.create_layout_handle,
            )

    @object_command('open_view_layout')
    async def open_view_layout(self):
        return htypes.layout_editor.view_layout_editor()
