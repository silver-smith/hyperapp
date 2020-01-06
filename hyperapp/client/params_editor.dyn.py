from collections import OrderedDict

from hyperapp.client.module import ClientModule

from . import htypes
from .record_object import RecordObject


class ParamsEditor(RecordObject):

    @classmethod
    async def from_data(cls, state, async_ref_resolver):
        target_piece = await async_ref_resolver.resolve_ref_to_object(state.target_piece_ref)
        fields = [(name, await async_ref_resolver.resolve_ref_to_object(piece_ref))
                  for name, piece_ref in state.fields]
        return cls(target_piece, state.target_command_id, fields)

    def __init__(self, target_piece, target_command_id, fields):
        super().__init__()
        self._target_piece = target_piece
        self._target_command_id = target_command_id
        self._fields = fields

    def get_title(self):
        return f"Parameters for {self._target_command_id}"

    def get_fields(self):
        return OrderedDict(self._fields)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._ref_registry = services.ref_registry
        self._field_types = services.field_types = {
            str: htypes.line.line(''),
            }
        services.params_editor = self._open_params_editor
        services.object_registry.register_type(
            htypes.params_editor.params_editor, ParamsEditor.from_data, services.async_ref_resolver)

    def _open_params_editor(self, piece, command, args, kw):
        bound_arguments = command.bound_arguments(*args, **kw)
        wanted_arguments = [
            (name, p.annotation) for name, p in bound_arguments.signature.parameters.items()
            if name not in bound_arguments.arguments
            ]
        fields = [
            htypes.params_editor.field(
                name,
                self._ref_registry.register_object(
                    self._annotation_to_field(annotation)),
                )
            for name, annotation in wanted_arguments]
        return htypes.params_editor.params_editor(
            target_piece_ref=self._ref_registry.register_object(piece),
            target_command_id=command.id,
            fields=fields,
            )

    def _annotation_to_field(self, annotation):
        return self._field_types[annotation]
