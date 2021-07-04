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

    @classmethod
    def record_field_dir(cls, field_id, field_object):
        return [*cls.dir_list[-1], htypes.record_object.record_field_d(field_id), *field_object.dir_list[-1]]


    @classmethod
    def record_field_dir_list(cls, field_id, field_object):
        # All dirs for object and one for us. todo: maybe, more than one for us.
        return [
            *field_object.dir_list,
            cls.record_field_dir(field_id, field_object),
            ]
