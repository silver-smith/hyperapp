from . import htypes
from .command import command
from .record_object import RecordObject
from .chooser import ChooserCallback, Chooser
from .module import ClientModule


class _ParamChooserCallback(ChooserCallback):

    def __init__(self, params_editor, field_id):
        self._params_editor = params_editor
        self._field_id = field_id

    async def element_chosen(self, key):
        return (await self._params_editor.field_element_chosen(self._field_id, key))


class ParamsEditor(RecordObject):

    @classmethod
    async def from_data(cls, state, mosaic, async_web, object_animator):
        target_piece = await async_web.summon(state.target_piece_ref)
        target_object = await object_animator.animate(target_piece)
        bound_arguments = {
            name: await async_web.summon(value_ref)
            for name, value_ref in state.bound_arguments
            }
        fields_pieces = {
            name: await async_web.summon(piece_ref)
            for name, piece_ref in state.fields
            }
        self = cls(mosaic, target_piece, target_object, state.target_command_id, bound_arguments)
        await self.async_init(object_animator, fields_pieces)
        return self

    def __init__(self, mosaic, target_piece, target_object, target_command_id, bound_arguments):
        super().__init__()
        self._mosaic = mosaic
        self._target_piece = target_piece
        self._target_object = target_object
        self._target_command_id = target_command_id
        self._bound_arguments = bound_arguments
        self._chooser = None
        self._chooser_callback = None

    async def async_init(self, object_animator, fields_pieces):
        await super().async_init(object_animator, fields_pieces)
        for field_id, field_object in self.fields.items():
            if isinstance(field_object, Chooser):
                callback = _ParamChooserCallback(self, field_id)
                field_object.chooser_set_callback(callback)
                self._chooser = field_object
                self._chooser_callback = callback
        if self._chooser:
            self._submit.disable()

    @property
    def type(self):
        if self._chooser:
            command_list = ()
        else:
            command_list=(
                htypes.object_type.object_command('submit', None),
                )
        return htypes.params_editor.params_editor_type(
            command_list=command_list,
            field_type_list=tuple(
                htypes.record_ot.field(
                    id=field_id,
                    object_type_ref=self._mosaic.put(field_object.type),
                    )
                for field_id, field_object in self.fields.items()
                ),
            )

    @property
    def title(self):
        return f"Parameters for {self._target_command_id}"

    @property
    def piece(self):
        return htypes.params_editor.params_editor(
            target_piece_ref=self._mosaic.put(self._target_piece),
            target_command_id=self._target_command_id,
            bound_arguments=[
                htypes.params_editor.bound_argument(
                    name, self._mosaic.put(value))
                for name, value in self._bound_arguments.items()
                ],
            fields=[
                htypes.params_editor.field(
                    name, self._mosaic.put(field_object.piece))
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

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_registry.register_actor(
            htypes.params_editor.params_editor, ParamsEditor.from_data,
            services.mosaic, services.async_web, services.object_animator)
