import abc

from . import htypes
from .object import Object


class RecordObject(Object, metaclass=abc.ABCMeta):

    type = htypes.record_object.record_object_type(command_list=(), field_type_list=())

    def __init__(self, fields=None):
        super().__init__()
        self.fields = fields

    async def async_init(self, object_animator, fields_pieces):
        self.fields = {
            name: await object_animator.animate(piece)
            for name, piece in fields_pieces.items()
            }
