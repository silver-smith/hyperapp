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

    type = htypes.code_command_chooser.code_command_chooser_type(
        command_list=(
            htypes.object_type.object_command('choose', None),
            ),
        )

    @classmethod
    async def from_state(cls, state, mosaic, async_ref_resolver, object_registry, object_layout_registry):
        piece = await async_ref_resolver.summon(state.piece_ref)
        object = await object_registry.animate(piece)
        layout_watcher = LayoutWatcher()  # todo: use global category/command -> watcher+layout handle registry
        layout = await object_layout_registry.invite(state.layout_ref, ['root'], layout_watcher)
        return cls(mosaic, object, layout)

    def __init__(self, mosaic, object, layout):
        super().__init__()
        self._mosaic = mosaic
        self._object = object
        self._layout = layout

    @property
    def title(self):
        return f"Commands for: {self._object.title}"

    @property
    def data(self):
        piece_ref = self._mosaic.put(self._object.data)
        layout_ref = self._mosaic.put(self._layout.data)
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
            for path, command in self._layout.available_code_commands(self._object)
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

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        services.object_registry.register_actor(
            htypes.code_command_chooser.code_command_chooser,
            CodeCommandChooser.from_state,
            services.mosaic,
            services.async_ref_resolver,
            services.object_registry,
            services.object_layout_registry,
            )
