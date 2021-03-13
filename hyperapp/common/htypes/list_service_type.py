from .htypes import Type, TList
from .record import TRecord
from .interface import Interface, Request


class ListServiceType(Type):

    def __init__(self, name, field_dict, row_t=None, interface=None):
        super().__init__(name)
        self._field_dict = field_dict
        self.row_t = row_t
        self.interface = interface

    def __str__(self):
        return f'ListServiceType({self.name})'

    def __repr__(self):
        return f'<ListServiceType {self.name!r} {self._field_dict}>'

    def __hash__(self):
        return id((self._name, self._field_dict))

    def __eq__(self, rhs):
        return (rhs is self
                or isinstance(rhs, ListServiceType)
                and rhs._name == self._name
                and rhs._field_dict == self._field_dict)

    @property
    def fields(self):
        return self._field_dict
