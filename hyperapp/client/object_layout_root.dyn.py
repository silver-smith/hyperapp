from hyperapp.client.command import command

from . import htypes
from .layout import InsertVisualItemDiff, RemoveVisualItemDiff, Layout
from .view_chooser import ViewFieldRef


class ObjectLayoutRoot(Layout):

    def __init__(self, object_layout_overrides, layout, piece_ref, object):
        super().__init__(path=[])
        self._object_layout_overrides = object_layout_overrides
        self._layout = layout
        self._piece_ref = piece_ref
        self._object = object

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
        resource_key = self._object.hashable_resource_key
        self._object_layout_overrides[resource_key] = view
        return htypes.layout_editor.object_layout_editor(self._piece_ref)
