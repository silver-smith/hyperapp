from hyperapp.client.command import command

from .layout import InsertVisualItemDiff, RemoveVisualItemDiff, Layout
from .view_chooser import ViewFieldRef


class ObjectLayoutRoot(Layout):

    def __init__(self, object_layout_resolver, layout_watcher, layout, object, command_hub, piece_opener):
        super().__init__(path=[])
        self._object_layout_resolver = object_layout_resolver
        self._layout_watcher = layout_watcher
        self._layout = layout
        self._object = object
        self._command_hub = command_hub
        self._piece_opener = piece_opener

    def get_view_ref(self):
        assert 0  # todo

    async def create_view(self):
        assert 0  # todo?

    async def visual_item(self):
        item = await self._layout.visual_item()
        return item.with_commands(super().get_current_commands())

    def get_current_commands(self):
        return self.__merge_commands(
            self._layout.get_current_commands(),
            super().get_current_commands(),
            )

    @command('replace')
    async def _replace_view(self, path, view: ViewFieldRef):
        layout = await self._object_layout_resolver.resolve(view, self._object, self._command_hub, self._piece_opener)
        self._layout = layout
        root_item = await self.visual_item()
        item = root_item.to_item(0, 'root')
        self._layout_watcher.distribute_diffs([RemoveVisualItemDiff([*self._path, 0])])
        self._layout_watcher.distribute_diffs([InsertVisualItemDiff(self._path, 0, item)])
