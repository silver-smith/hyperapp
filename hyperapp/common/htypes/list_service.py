from .htypes import Type, TList
from .record import TRecord
from .interface import Interface, Request


class ListService(Type):

    def __init__(self, name, field_dict, interface):
        super().__init__(name)
        self._field_dict = field_dict
        self._interface = interface

    def __str__(self):
        return f'ListService({self.name})'

    def __repr__(self):
        return f'<ListService {self.name!r} {self._field_dict}>'

    def __hash__(self):
        return id((self._name, self._field_dict))

    def __eq__(self, rhs):
        return (rhs is self
                or isinstance(rhs, ListService)
                and rhs._name == self._name
                and rhs._field_dict == self._field_dict)

    @property
    def fields(self):
        return self._field_dict

    @property
    def interface(self):
        return self._interface
