from functools import cached_property

from hyperapp.common.module import Module

from . import htypes


class ListAdapter:

    @classmethod
    async def from_piece(cls, impl, piece, python_object_creg):
        dir = python_object_creg.invite(impl.dir)
        ctr = python_object_creg.invite(impl.function)
        object = ctr(piece)
        return cls(dir, object, impl.key_attribute)

    def __init__(self, dir, object, key_attribute):
        self._dir = dir
        self._object = object
        self._key_attribute = key_attribute
        self._columns = []

    @property
    def dir_list(self):
        return [
            [htypes.list_object.list_object_d()],
            [self._dir],
            ]

    @property
    def object(self):
        return self._object

    @property
    def key_attribute(self):
        return self._key_attribute

    @property
    def title(self):
        return 'todo: title'

    @property
    def command_list(self):
        return []

    @property
    def columns(self):
        self._rows  # Load columns.
        return self._columns

    @property
    def row_count(self):
        return len(self._rows)

    def row(self, idx):
        return self._rows[idx]

    @cached_property
    def _rows(self):
        row_list = []
        for item in self._object.get():
            row = {}
            for name in sorted(dir(item)):
                if name.startswith('_'):
                    continue
                value = getattr(item, name)
                if callable(value):
                    continue
                row[name] = value
                if name not in self._columns:
                    self._columns.append(name)
            row_list.append(row)
        return row_list


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.adapter_registry.register_actor(htypes.impl.list_impl, ListAdapter.from_piece, services.python_object_creg)
