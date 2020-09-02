import abc

from hyperapp.client.object import Object

from . import htypes


class RecordObject(Object, metaclass=abc.ABCMeta):

    type = htypes.record_object.record_object_type(command_list=(), field_type_list=())

    async def async_init(self, object_registry, fields_pieces):
        self.fields = {
            name: await object_registry.resolve_async(piece)
            for name, piece in fields_pieces.items()
            }
