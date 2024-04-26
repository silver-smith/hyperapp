
class Context:

    def __init__(self, items=None, **kw):
        self._items = {**kw, **(items or {})}

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return self._items[name]

    def clone_with(self, **kw):
        return Context({**self._items, **kw})

    def as_dict(self):
        return self._items
