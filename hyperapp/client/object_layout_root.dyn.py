from hyperapp.client.command import command

from .layout import Layout
from .view_chooser import ViewFieldRef


class ObjectLayoutRoot(Layout):

    def __init__(self, layout):
        super().__init__(path=[])
        self._layout = layout

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
        assert 0, view
