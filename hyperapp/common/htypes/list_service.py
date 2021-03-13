from .htypes import Type, TList, tString
from .record import TRecord, ref_t
from .interface import Interface, Request


class ListServiceType(Type):

    def __init__(self, name, field_dict, row_t=None, interface=None):
        super().__init__(name)
        self._field_dict = field_dict  # name -> t
        self.row_t = row_t
        self.interface = interface

    def __str__(self):
        return f'ListServiceType({self.name})'

    def __repr__(self):
        return f'<ListServiceType {self.name!r} {self._field_dict}>'

    def __hash__(self):
        return hash((self._name, tuple(self._field_dict.items())))

    def __eq__(self, rhs):
        return (rhs is self
                or isinstance(rhs, ListServiceType)
                and rhs._name == self._name
                and rhs._field_dict == self._field_dict)

    @property
    def fields(self):
        return self._field_dict


list_service_t = TRecord('list_service', {
    'type_ref': ref_t,  # list service type
    'peer_ref': ref_t,
    'object_id': tString,
    'key_field': tString,
    })


def register_list_service_types(builtin_types, mosaic, types):
    builtin_types.register(mosaic, types, list_service_t)
