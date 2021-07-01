import inspect

from . import htypes


class BuiltinCommand:

    @classmethod
    def from_method(cls, object, method):
        attr_name = method.__name__
        wanted_params = {
            name for name
            in inspect.signature(method).parameters
            if name != 'self'
            }
        return cls(object.dir_list[-1], method, attr_name, wanted_params)

    def __init__(self, object_dir, method, name, wanted_params):
        self._object_dir = object_dir
        self._method = method
        self.name = name
        self._wanted_params = wanted_params

    @property
    def dir(self):
        return [*self._object_dir, htypes.command.builtin_object_command_d(self.name)]

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
            raise RuntimeError(f"Method {self.name!r} wants arguments {missing_kw} but {view_state!r} does not provide them")
        return await self._method(**kw)


class Command:

    @classmethod
    def from_fn(cls, module_name, fn, name=None):
        if not name:
            name = fn.__name__

        def from_piece(piece):
            return cls(module_name, name, fn)

        return from_piece

    def __init__(self, module_name, name, fn):
        self._module_name = module_name
        self.name = name
        self._fn = fn

    @property
    def dir(self):
        return [htypes.command.context_object_command_d(self._module_name, self.name)]

    async def run(self, object, view_state):
        return await self._fn(object, view_state)
