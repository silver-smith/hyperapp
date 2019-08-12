import abc

from hyperapp.client.object import Object


class RecordObject(Object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_fields(self):
        pass
