import abc
from collections import namedtuple

from hyperapp.client.object import Object


Field = namedtuple('Field', 'piece object')


class RecordObject(Object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_fields(self):
        pass
