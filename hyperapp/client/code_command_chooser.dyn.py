from collections import namedtuple

from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .chooser import Chooser
from .column import Column
from .layout_handle import LayoutWatcher
from .simple_list_object import SimpleListObject


class CommandIdField:
    pass


Item = namedtuple('Item', 'path id kind')


class CodeCommandChooser(SimpleListObject, Chooser):

    @classmethod
    async def from_state(cls, state, ref_registry, async_ref_resolver, object_registry, object_layout_resolver):
        piece = await async_ref_resolver.resolve_ref_to_object(state.piece_ref)
        object = await object_registry.resolve_async(piece)
        layout_watcher = LayoutWatcher()  # todo: use global category/command -> watcher+layout handle registry
        layout = await object_layout_resolver.resolve(state.layout_ref, ['root'], object, layout_watcher)
        return cls(ref_registry, object, layout)

    def __init__(self, ref_registry, object, layout):
        super().__init__()
        self._ref_registry = ref_registry
        self._object = object
        self._layout = layout

    @property
    def title(self):
        return f"Commands for: {self._object.title}"

    @property
    def data(self):
        piece_ref = self._ref_registry.register_object(self._object.data)
        layout_ref = self._ref_registry.register_object(self._layout.data)
        return htypes.code_command_chooser.code_command_chooser(piece_ref, layout_ref)

    @property
    def columns(self):
        return [
            Column('path'),
            Column('id', is_key=True),
            Column('kind'),
            ]

    async def get_all_items(self):
        return [
            Item('', 'self', ''),
            ] +[
            await self._make_item(path, command)
            for path, command in self._layout.collect_view_commands()
            ]

    async def _make_item(self, path, command):
        return Item('/' + '/'.join(path), command.id, command.kind)

    def get_value(self):
        return None

    @command('choose', kind='element')
    async def _choose(self, item_key):
        command_id = item_key
        return (await self.chooser_call_callback(command_id))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.code_command_chooser.code_command_chooser,
            CodeCommandChooser.from_state,
            services.ref_registry,
            services.async_ref_resolver,
            services.object_registry,
            services.object_layout_resolver,
            )
