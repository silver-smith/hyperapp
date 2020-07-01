import abc
from collections import namedtuple

from hyperapp.client.object import Object


class RecordObject(Object, metaclass=abc.ABCMeta):

    category_list = ['record']

    # Returns (ordered) dict name -> object
    @abc.abstractproperty
    def fields(self):
        pass
