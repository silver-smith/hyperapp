from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .record_object import RecordObject
from .chooser import ChooserCallback, Chooser


class _ParamChooserCallback(ChooserCallback):

    def __init__(self, params_editor, field_id):
        self._params_editor = params_editor
        self._field_id = field_id

    async def element_chosen(self, key):
        return (await self._params_editor.field_element_chosen(self._field_id, key))


class ParamsEditor(RecordObject):

    @classmethod
    async def from_data(cls, state, ref_registry, async_ref_resolver, object_registry):
        target_piece = await async_ref_resolver.resolve_ref_to_object(state.target_piece_ref)
        target_object = await object_registry.resolve_async(target_piece)
        bound_arguments = {
            name: await async_ref_resolver.resolve_ref_to_object(value_ref)
            for name, value_ref in state.bound_arguments
            }
        fields_pieces = {
            name: await async_ref_resolver.resolve_ref_to_object(piece_ref)
            for name, piece_ref in state.fields
            }
        self = cls(ref_registry, target_piece, target_object, state.target_command_id, bound_arguments)
        await self.async_init(object_registry, fields_pieces)
        return self

    def __init__(self, ref_registry, target_piece, target_object, target_command_id, bound_arguments):
        super().__init__()
        self._ref_registry = ref_registry
        self._target_piece = target_piece
        self._target_object = target_object
        self._target_command_id = target_command_id
        self._bound_arguments = bound_arguments
        self._chooser_callback_list = []

    async def async_init(self, object_registry, fields_pieces):
        await super().async_init(object_registry, fields_pieces)
        for field_id, field_object in self.fields.items():
            if isinstance(field_object, Chooser):
                callback = _ParamChooserCallback(self, field_id)
                field_object.chooser_set_callback(callback)
                self._chooser_callback_list.append(callback)
        if self._chooser_callback_list:
            self._submit.disable()

    def get_title(self):
        return f"Parameters for {self._target_command_id}"

    @property
    def data(self):
        return htypes.params_editor.params_editor(
            target_piece_ref=self._ref_registry.register_object(self._target_piece),
            target_command_id=self._target_command_id,
            bound_arguments=[
                htypes.params_editor.bound_argument(
                    name, self._ref_registry.register_object(value))
                for name, value in self._bound_arguments.items()
                ],
            fields=[
                htypes.params_editor.field(
                    name, self._ref_registry.register_object(field_object.data))
                for name, field_object in self.fields.items()
                ],
            )

    async def field_element_chosen(self, field_id, key):
        values = self._collect_values()
        return (await self._run_command(values={**values, field_id: key}))

    @command('submit')
    async def _submit(self):
        return (await self._run_command(self._collect_values()))

    # todo: add other, predefined, values (element key)
    def _collect_values(self):
        field_values = {
            id: field_object.get_value()
            for id, field_object in self.fields.items()
            }
        return {
            **self._bound_arguments,
            **field_values,
            }

    async def _run_command(self, values):
        command = self._target_object.get_command(self._target_command_id)
        return (await command.run_with_full_params(**values))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.params_editor.params_editor, ParamsEditor.from_data,
            services.ref_registry, services.async_ref_resolver, services.object_registry)
