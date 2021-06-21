import inspect


# decorator for object methods
class command:

    def __init__(self, id, kind=None):
        self.id = id

    def __call__(self, class_method):
        return Command(self.id, class_method)


class Command:

    def __init__(self, id, class_method):
        self.id = id
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
