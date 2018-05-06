from .htypes import Type


class TypeNamespace(object):

    def __init__(self, **kw):
        self._items = {}
        for key, value in kw.items():
            self[key] = value

    def get(self, name):
        return self._items.get(name)

    def keys(self):
        return self._items.keys()

    def __setitem__(self, name, value):
        assert isinstance(name, str), repr(name)
        assert isinstance(value, (Type, TypeNamespace)), repr((name, value))
        self._items[name] = value

    def __contains__(self, name):
        return name in self._items

    def __getitem__(self, name):
        return self._items[name]

    def __getattr__(self, name):
        value = self.get(name)
        if value is None:
            raise AttributeError(name)
        else:
            return value
