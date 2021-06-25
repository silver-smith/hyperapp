import inspect

from hyperapp.common.module import Module

from . import htypes


class BuiltinCommand:

    @classmethod
    def from_class_method(cls, method):
        module_ref = inspect.getmodule(method).__module_ref__
        qual_name = method.__qualname__
        attr_name = method.__name__
        wanted_params = {
            name for name
            in inspect.signature(method).parameters
            if name != 'self'
            }
        return cls(module_ref, qual_name, attr_name, wanted_params)
        
    @classmethod
    def from_piece(cls, piece):
        return cls(piece.module_ref, piece.qual_name, piece.name, set(piece.wanted_params))

    def __init__(self, module_ref, qual_name, name, wanted_params):
        self._module_ref = module_ref
        self._qual_name = qual_name
        self.name = name
        self._wanted_params = wanted_params

    @property
    def piece(self):
        return htypes.command.builtin_command(
            self._module_ref, self._qual_name, self.name, list(self._wanted_params))

    async def run(self, object, view_state):
        kw = {
            name: getattr(view_state, name)
            for name in object.view_state_fields
            if name in self._wanted_params
            }
        if 'view_state' in self._wanted_params:
            kw['view_state'] = view_state
        missing_kw = self._wanted_params - set(kw)
        if missing_kw:
            raise RuntimeError(f"Method {self._class_method} wants arguments {missing_kw} but {view_state!r} does not provide them")
        method = getattr(object, self.name)
        return await method(**kw)


class Command:

    @classmethod
    def from_fn(cls, fn, name=None):
        if not name:
            name = fn.__name__

        def from_piece(piece):
            return cls(name, piece, fn)

        return from_piece

    def __init__(self, name, piece, fn):
        self.name = name
        self.piece = piece
        self._fn = fn

    async def run(self, object, view_state):
        return await self._fn(object, view_state)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.command_registry.register_actor(htypes.command.builtin_command, BuiltinCommand.from_piece)
