from hyperapp.client.command import command

from . import htypes
from .layout import InsertVisualItemDiff, RemoveVisualItemDiff, Layout
from .view_chooser import LayoutRecMakerField


class ObjectLayoutRoot(Layout):

    def __init__(self, ref_registry, object_layout_association, layout, piece_ref, object):
        super().__init__(path=[])
        self._ref_registry = ref_registry
        self._object_layout_association = object_layout_association
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
    async def _replace_view(self, path):
        category = self._object.category_list[0]
        chooser = htypes.view_chooser.view_chooser(category)
        chooser_ref = self._ref_registry.register_object(chooser)
        layout_rec_maker_field = htypes.params_editor.field('layout_rec_maker', chooser_ref)
        return htypes.params_editor.params_editor(
            target_piece_ref=self._ref_registry.register_object(self._object.data),  # todo: use layout editor here
            target_command_id=self._replace_impl.id,
            bound_arguments=[],
            fields=[layout_rec_maker_field],
            )

    @command('_replace_impl')
    async def _replace_impl(self, path, layout_rec_maker: LayoutRecMakerField):
        resource_key = self._object.hashable_resource_key
        layout_rec = await layout_rec_maker(self._object)
        layout_ref = self._ref_registry.register_object(layout_rec)
        self._object_layout_association[self._object.category_list[-1]] = layout_ref
        return htypes.layout_editor.object_layout_editor(self._piece_ref)
