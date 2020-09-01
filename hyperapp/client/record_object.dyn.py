import abc
from dataclasses import dataclass, field
from collections import namedtuple
from typing import Dict

from hyperapp.client.object import ObjectType, Object

from . import htypes


@dataclass
class RecordObjectType(ObjectType):
    fields: Dict[str, ObjectType] = field(default_factory=dict)


class RecordObject(Object, metaclass=abc.ABCMeta):

    type = htypes.record_object.record_object_type(command_list=(), field_type_list=())

    async def async_init(self, object_registry, fields_pieces):
        self.fields = {
            name: await object_registry.resolve_async(piece)
            for name, piece in fields_pieces.items()
            }
