import abc

from . import htypes
from .object import Object


class RecordObject(Object, metaclass=abc.ABCMeta):

    dir_list = [
        *Object.dir_list,
        [htypes.record_object.record_object_d()],
        ]

    def __init__(self, fields=None):
        super().__init__()
        self.fields = fields

    async def async_init(self, object_factory, fields_pieces):
        self.fields = {
            name: await object_factory.animate(piece)
            for name, piece in fields_pieces.items()
            }
