
class Context:

    def __init__(self, items=None):
        self._items = items or {}

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return self._items[name]

    def clone_with(self, **kw):
        return Context({**self._items, **kw})
