from hyperapp.common.module import Module

from . import htypes


class ListAdapter:

    @classmethod
    async def from_piece(cls, piece, python_object_creg):
        dir = python_object_creg.invite(piece.dir)
        return cls(dir, piece.key_attribute)

    def __init__(self, dir, key_attribute):
        self._dir = dir
        self._key_attribute = key_attribute

    @property
    def dir_list(self):
        return [
            [htypes.list_object.list_object_d()],
            [self._dir],
            ]

    @property
    def key_attribute(self):
        return self._key_attribute

    @property
    def title(self):
        return 'todo: title'

    @property
    def command_list(self):
        return []


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.adapter_registry.register_actor(htypes.impl.list_impl, ListAdapter.from_piece, services.python_object_creg)
