from . import htypes
from .code.rc_requirement import Requirement


class TypeReq(Requirement):

    @classmethod
    def from_type_src(cls, type_src):
        return cls(type_src.module_name, type_src.name)

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            name=piece.name,
            )

    def __init__(self, module_name, name):
        self._module_name = module_name
        self._name = name

    def __str__(self):
        return f"TypeReq({self._module_name}.{self._name})"

    def __eq__(self, rhs):
        return (type(rhs) == TypeReq
                and rhs._module_name == self._module_name
                and rhs._name == self._name)

    def __hash__(self):
        return hash(('type_req', self._module_name, self._name))

    @property
    def piece(self):
        return htypes.type_resource.type_req(
            module_name=self._module_name,
            name=self._name,
            )

    @property
    def desc(self):
        return f"{self._module_name}.{self._name} type"

    def get_target(self, target_factory):
        return target_factory.type(self._module_name, self._name)

    def make_resource(self, target):
        return target.resource
