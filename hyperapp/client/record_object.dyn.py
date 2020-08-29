import abc
from dataclasses import dataclass, field
from collections import namedtuple
from typing import Dict

from hyperapp.client.object import ObjectType, Object


@dataclass
class RecordObjectType(ObjectType):
    fields: Dict[str, ObjectType] = field(default_factory=dict)


class RecordObject(Object, metaclass=abc.ABCMeta):

    type = RecordObjectType(['record'])
    category_list = ['record']

    async def async_init(self, object_registry, fields_pieces):
        self.fields = {
            name: await object_registry.resolve_async(piece)
            for name, piece in fields_pieces.items()
            }
