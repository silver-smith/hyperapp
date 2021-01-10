import logging
from collections import namedtuple

from ..util import is_list_inst, is_dict_inst
from .htypes import Type

log = logging.getLogger(__name__)


Request = namedtuple('Request', 'method_name params_record_t response_record_t')
Notification = namedtuple('Notification', 'method_name params_record_t')


class Interface(Type):

    def __init__(self, name, base=None, method_list=None):
        assert base is None or isinstance(base, Interface), repr(base)
        assert is_list_inst(method_list or [], (Request, Notification)), repr(method_list)
        super().__init__(name)
        self._base = base
        self._method_dict = {method.method_name: method for method in method_list}

    def __str__(self):
        return f'Interface({self.name})'

    def __repr__(self):
        return f'<Interface {self.name!r} {self._method_dict}>'

    def __hash__(self):
        return id(self)

    def __eq__(self, rhs):
        return (rhs is self
                or isinstance(rhs, Interface)
                and (self._base is rhs._base is None or rhs._base.match(self._base))
                and rhs._method_dict == self._method_dict)
