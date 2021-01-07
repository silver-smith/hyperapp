from hyperapp.client.module import ClientModule

from . import htypes


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        self._mosaic = services.mosaic
        self._async_ref_resolver = services.async_ref_resolver
        self._field_types = services.field_types = {
            str: htypes.line.line(''),
            }
        services.params_editor = self._open_params_editor

    async def _open_params_editor(self, piece, command, bound_arguments_sig, args, kw):
        bound_arguments = [
            htypes.params_editor.bound_argument(name, self._mosaic.distil(value))
            for name, value in bound_arguments_sig.arguments.items()
            if name != 'self'
            ]
        wanted_arguments = [
            (name, p.annotation)
            for name, p in bound_arguments_sig.signature.parameters.items()
            if name not in bound_arguments_sig.arguments
            ]
        fields = [
            htypes.params_editor.field(
                name,
                self._mosaic.distil(
                    self._annotation_to_field(name, annotation)),
                )
            for name, annotation in wanted_arguments]
        return htypes.params_editor.params_editor(
            target_piece_ref=self._mosaic.distil(piece),
            target_command_id=command.id,
            bound_arguments=bound_arguments,
            fields=fields,
            )

    def _annotation_to_field(self, name, annotation):
        try:
            return self._field_types[annotation]
        except KeyError as x:
            raise RuntimeError(f"No annotation is defined for field {name!r}: {x}")
