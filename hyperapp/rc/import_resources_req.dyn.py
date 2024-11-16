from . import htypes
from .code.rc_requirement import Requirement


class ImportResourcesReq(Requirement):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            )

    def __init__(self, module_name):
        self._module_name = module_name

    def __str__(self):
        return f"ImportResReq({self._module_name})"

    def __eq__(self, rhs):
        return (type(rhs) == ImportResourcesReq
                and rhs._module_name == self._module_name)

    def __hash__(self):
        return hash(('type_resources_req', self._module_name))

    @property
    def piece(self):
        return htypes.import_resources_req.import_resources_req(
            module_name=self._module_name,
            )

    @property
    def desc(self):
        return f"{self._module_name} resources"
