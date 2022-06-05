from functools import cached_property

from hyperapp.common.htypes import tInt, tString
from hyperapp.common.module import Module

from . import htypes


class ListAdapter:

    @classmethod
    async def from_spec(cls, spec, piece, object, python_object_creg):
        title = str(piece)
        key_t = python_object_creg.invite(spec.key_t)
        dir = python_object_creg.invite(spec.dir)
        return cls(dir, object, title, spec.key_attribute, key_t)

    def __init__(self, dir, object, title, key_attribute, key_t):
        self._dir = dir
        self._object = object
        self._title = title
        self._key_attribute = key_attribute
        self._key_t = key_t
        self._columns = []

    @property
    def dir_list(self):
        return [
            [htypes.list.list_d()],
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
        return self._title

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

    @cached_property
    def idx_to_id(self):
        return {
            idx: row[self._key_attribute]
            for idx, row
            in enumerate(self._rows)
            }

    @cached_property
    def id_to_idx(self):
        return {
            row[self._key_attribute]: idx
            for idx, row
            in enumerate(self._rows)
            }

    @cached_property
    def state_t(self):
        # todo: construct state from key_t.
        if self._key_t is tInt:
            return htypes.list.int_state
        if self._key_t is tString:
            return htypes.list.string_state
        raise RuntimeError(f"{self.__class__.__name__}: Unsupported key type: {self._key_t}")


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.adapter_registry.register_actor(
            htypes.impl.list_spec, ListAdapter.from_spec, services.python_object_creg)
