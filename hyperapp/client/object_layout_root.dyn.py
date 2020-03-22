from hyperapp.client.command import command

from .layout import Layout
from .view_chooser import ViewFieldRef


class ObjectLayoutRoot(Layout):

    def __init__(self, layout):
        self._layout = layout

    def get_view_ref(self):
        assert 0  # todo

    async def create_view(self):
        assert 0  # todo?

    async def visual_item(self):
        return (await self._layout.visual_item())

    def get_current_commands(self):
        return self.__merge_commands(
            layout.get_current_commands(),
            super().get_current_commands(),
            )

    @command('replace')
    async def _replace_view(self, view: ViewFieldRef):
        assert 0, view
