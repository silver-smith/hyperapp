import inspect


class Context:

    def __init__(self, items=None, next=None, **kw):
        self._next = next
        self._items = {**kw, **(items or {})}

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if self._next and name in self._next:
            return getattr(self._next, name)
        return self._items[name]

    def __contains__(self, name):
        if self._next:
            if name in self._next:
                return True
        return name in self._items

    def clone_with(self, **kw):
        return Context({**self._items, **kw}, self._next)

    def copy_from(self, ctx):
        return Context({**self._items, **ctx._items}, self._next)

    def push(self, **kw):
        return Context(kw.copy(), self)

    def pop(self):
        return self._next

    def diffs(self, rhs):
        diffs = set()
        for name, lvalue in self._items.items():
            try:
                rvalue = rhs._items[name]
            except KeyError:
                diffs.add(name)
            else:
                if rvalue != lvalue:
                    diffs.add(name)
        for name in rhs._items:
            if name not in self._items:
                diffs.add(name)
        return diffs

    def as_dict(self):
        if self._next:
            return {**self._next.as_dict(), **self._items}
        else:
            return self._items

    @staticmethod
    def attributes(obj):
        return {
            name: getattr(obj, name)
            for name in dir(obj)
            if (not name.startswith('_')
                and not inspect.isbuiltin(getattr(obj, name)))
            }
