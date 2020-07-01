import abc
from collections import namedtuple

from hyperapp.client.object import Object


class RecordObject(Object, metaclass=abc.ABCMeta):

    category_list = ['record']

    async def async_init(self, object_registry, fields_pieces):
        self.fields = {
            name: await object_registry.resolve_async(piece)
            for name, piece in fields_pieces.items()
            }
