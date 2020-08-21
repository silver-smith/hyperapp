from collections import namedtuple

from hyperapp.common.util import single
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .object_command import command as object_command
from .layout import LayoutWatcher
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'path id kind layout')


class CommandList(SimpleListObject):

    @classmethod
    async def from_state(cls, state, ref_registry, async_ref_resolver, object_registry, object_layout_resolver, object_layout_producer):
        piece = await async_ref_resolver.resolve_ref_to_object(state.piece_ref)
        object = await object_registry.resolve_async(piece)
        layout_watcher = LayoutWatcher()  # todo: use global category/command -> watcher+layout handle registry
        layout = await object_layout_resolver.resolve(state.layout_ref, [0], object, layout_watcher)
        return cls(ref_registry, object_registry, object_layout_producer, object, layout)

    def __init__(self, ref_registry, object_registry, object_layout_producer, object, layout):
        super().__init__()
        self._ref_registry = ref_registry
        self._object_registry = object_registry
        self._object_layout_producer = object_layout_producer
        self._object = object
        self._layout = layout

    def get_title(self):
        return f"Commands for: {self._object.get_title()}"

    @property
    def data(self):
        piece_ref = self._ref_registry.register_object(self._object.data)
        layout_ref = self._ref_registry.register_object(self._layout.data)
        return htypes.command_list.command_list(piece_ref, layout_ref)

    def get_columns(self):
        return [
            Column('path'),
            Column('id', is_key=True),
            Column('kind'),
            Column('layout'),
            ]

    async def get_all_items(self):
        return [
            await self._make_item(path, command)
            for path, command_list in self._layout.collect_view_commands().items()
            for command in command_list
            ]

    async def _make_item(self, path, command):
        resolved_piece = await self._run_command(command)
        if resolved_piece is not None:
            item = await resolved_piece.layout.visual_item()
            layout_str = item.text
        else:
            layout_str = ''
        return Item('/' + '/'.join(path), command.id, command.kind, layout_str)

    async def _run_command(self, command):
        if command.kind == 'element':
            item = await self._object.load_first_item()
            args = [getattr(item, self._object.key_attribute)]
        else:
            args = []
        resolved_piece = await command.run(*args)
        return resolved_piece

    def _command_by_id(self, command_id):
        return single(
            command
            for command_list in self._layout.collect_view_commands().values()
            for command in command_list
            if command.id == command_id
            )

    @command('run', kind='element')
    async def _run(self, item_key):
        # todo: pass current item to command list, use it here for element commands.
        command = self._command_by_id(item_key)
        return (await self._run_command(command))

    @object_command('layout', kind='element')
    async def _open_layout(self, item_key):
        command = self._command_by_id(item_key)
        resolved_piece = await self._run_command(command)
        if resolved_piece is None:
            return None
        piece_ref = self._ref_registry.register_object(resolved_piece.object.data)
        layout_ref = self._ref_registry.register_object(resolved_piece.layout.data)
        category = self._object.category_list[-1]
        return htypes.layout_editor.object_layout_editor(piece_ref, layout_ref, category, command.id)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.command_list.command_list,
            CommandList.from_state,
            services.ref_registry,
            services.async_ref_resolver,
            services.object_registry,
            services.object_layout_resolver,
            services.object_layout_producer,
            )
