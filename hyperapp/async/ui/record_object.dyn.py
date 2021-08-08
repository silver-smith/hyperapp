import abc

from . import htypes
from .object import Object


def record_field_dir(record_dir, field_id, field_object):
    return [*record_dir, htypes.record_object.record_field_d(field_id), *field_object.dir_list[-1]]


def record_field_add_dir_list(record_dir_list, field_id, field_object):
    return [
        record_field_dir(dir, field_id, field_object)
        for dir in record_dir_list
        ]


class RecordObject(Object, metaclass=abc.ABCMeta):

    dir_list = [
        *Object.dir_list,
        [htypes.record_object.record_object_d()],
        ]

    def __init__(self, fields=None):
        super().__init__()
        self.fields = fields  # field id -> field object

    async def async_init(self, object_factory, fields_pieces):
        self.fields = {
            id: await object_factory.animate(piece)
            for id, piece in fields_pieces.items()
            }
