from .htypes import Type


class TypeNamespace(object):

    def __init__(self, **kw):
        self._items = {}
        for key, value in kw.items():
            self[key] = value

    @property
    def name(self):
        if self.full_name:
            return self.full_name[-1]
        else:
            return None

    def get(self, name):
        return self._items.get(name)

    def keys(self):
        return self._items.keys()

    def items(self):
        return self._items.items()

    def resolve(self, full_name):
        assert full_name
        try:
            value = self[full_name[0]]
        except KeyError as x:
            raise RuntimeError('Unknown type name: %r' % full_name[0])
        if len(full_name) == 1:
            return value
        assert isinstance(value, TypeNamespace)
        return value.resolve(full_name[1:])

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
