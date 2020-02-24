from collections import OrderedDict

from hyperapp.client.module import ClientModule

from . import htypes
from .record_object import Field, RecordObject
from .chooser_observer import ChooserObserver, ChooserSubject


class _ParamChooserObserver(ChooserObserver):

    def __init__(self, params_editor, field_id):
        self._params_editor = params_editor
        self._field_id = field_id

    async def element_chosen(self, key):
        await self._params_editor.field_element_chosen(self._field_id, key)


class ParamsEditor(RecordObject):

    @classmethod
    async def from_data(cls, state, async_ref_resolver, object_registry):
        target_piece = await async_ref_resolver.resolve_ref_to_object(state.target_piece_ref)
        target_object = await object_registry.resolve_async(target_piece)
        fields = OrderedDict([(name, await cls._make_field(piece_ref, async_ref_resolver, object_registry))
                              for name, piece_ref in state.fields])
        return cls(object_registry, target_piece, target_object, state.target_command_id, fields)

    @staticmethod
    async def _make_field(piece_ref, async_ref_resolver, object_registry):
        piece = await async_ref_resolver.resolve_ref_to_object(piece_ref)
        object = await object_registry.resolve_async(piece)
        return Field(piece, object)

    def __init__(self, object_registry, target_piece, target_object, target_command_id, field_odict):
        super().__init__()
        self._object_registry = object_registry
        self._target_piece = target_piece
        self._target_object = target_object
        self._target_command_id = target_command_id
        self._field_odict = field_odict  # OrderedDict id -> Field
        self._observers = []
        for field_id, field in field_odict.items():
            if isinstance(field.object, ChooserSubject):
                observer = _ParamChooserObserver(self, field_id)
                field.object.chooser_subscribe(observer)
                self._observers.append(observer)

    def get_title(self):
        return f"Parameters for {self._target_command_id}"

    def get_fields(self):
        return self._field_odict

    async def field_element_chosen(self, field_id, key):
        # todo: add other field's values
        # todo: add other, predefined, values (element key)
        values = {field_id: key}
        command = self._target_object.get_command(self._target_command_id)
        return (await command.run(**values))


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
            htypes.params_editor.params_editor, ParamsEditor.from_data, services.async_ref_resolver, services.object_registry)

    async def _open_params_editor(self, piece, command, args, kw):
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
