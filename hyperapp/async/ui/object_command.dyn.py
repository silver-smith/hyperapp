import inspect


# decorator for object methods
class command:

    def __init__(self, name, kind=None):
        self.name = name

    def __call__(self, class_method):
        return BuiltinCommand(self.name, class_method)


class BuiltinCommand:

    def __init__(self, name, class_method):
        self.name = name
        self._class_method = class_method
        self._wanted_kw = {
            name for name
            in inspect.signature(class_method).parameters
            if name != 'self'
            }

    async def run(self, object, view_state):
        kw = {
            name: getattr(view_state, name)
            for name in object.view_state_fields
            if name in self._wanted_kw
            }
        missing_kw = self._wanted_kw - set(kw)
        if missing_kw:
            raise RuntimeError(f"Method {self._class_method} wants arguments {missing_kw} but {view_state!r} does not provide them")
        return await self._class_method(object, **kw)


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
        return await self._fn(object)
