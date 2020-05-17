from collections import OrderedDict

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .record_object import Field, RecordObject
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
        fields = OrderedDict([
            (name, await cls._make_field(piece_ref, async_ref_resolver, object_registry))
            for name, piece_ref in state.fields
            ])
        return cls(ref_registry, object_registry, target_piece, target_object, state.target_command_id, bound_arguments, fields)

    @staticmethod
    async def _make_field(piece_ref, async_ref_resolver, object_registry):
        piece = await async_ref_resolver.resolve_ref_to_object(piece_ref)
        object = await object_registry.resolve_async(piece)
        return Field(piece, object)

    def __init__(self, ref_registry, object_registry, target_piece, target_object, target_command_id, bound_arguments, field_odict):
        super().__init__()
        self._ref_registry = ref_registry
        self._object_registry = object_registry
        self._target_piece = target_piece
        self._target_object = target_object
        self._target_command_id = target_command_id
        self._bound_arguments = bound_arguments
        self._field_odict = field_odict  # OrderedDict id -> Field
        self._chooser_callback_list = []
        for field_id, field in field_odict.items():
            if isinstance(field.object, Chooser):
                callback = _ParamChooserCallback(self, field_id)
                field.object.chooser_set_callback(callback)
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
                    name, self._ref_registry.register_object(field.object.data))
                for name, field in self._field_odict.items()
                ],
            )

    def get_fields(self):
        return self._field_odict

    async def field_element_chosen(self, field_id, key):
        values = self._collect_values()
        return (await self._run_command(values={**values, field_id: key}))

    @command('submit')
    async def _submit(self):
        return (await self._run_command(self._collect_values()))

    # todo: add other, predefined, values (element key)
    def _collect_values(self):
        field_values = {
            id: field.object.get_value()
            for id, field in self._field_odict.items()
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
        self._ref_registry = services.ref_registry
        self._async_ref_resolver = services.async_ref_resolver
        self._field_types = services.field_types = {
            str: htypes.line.line(''),
            }
        services.params_editor = self._open_params_editor
        services.object_registry.register_type(
            htypes.params_editor.params_editor, ParamsEditor.from_data,
            services.ref_registry, services.async_ref_resolver, services.object_registry)

    async def _open_params_editor(self, piece, command, bound_arguments_sig, args, kw):
        bound_arguments = [
            htypes.params_editor.bound_argument(name, self._ref_registry.register_object(value))
            for name, value in bound_arguments_sig.arguments.items()
            if name != 'self'
            ]
        wanted_arguments = [
            (name, p.annotation) for name, p in bound_arguments_sig.signature.parameters.items()
            if name not in bound_arguments_sig.arguments
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
            bound_arguments=bound_arguments,
            fields=fields,
            )

    def _annotation_to_field(self, annotation):
        return self._field_types[annotation]
