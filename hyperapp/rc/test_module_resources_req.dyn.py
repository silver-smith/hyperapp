from . import htypes
from .code.rc_requirement import Requirement


class TestModuleResourcesReq(Requirement):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            )

    def __init__(self, module_name):
        self._module_name = module_name

    def __str__(self):
        return f"TestModuleResourcesReq({self._module_name})"

    def __eq__(self, rhs):
        return (type(rhs) == TestModuleResourcesReq
                and rhs._module_name == self._module_name)

    def __hash__(self):
        return hash(('test-module-resources-req', self._module_name))

    @property
    def piece(self):
        return htypes.test_module_resources_req.test_module_resources_req(
            module_name=self._module_name,
            )

    @property
    def desc(self):
        return f"{self._module_name} resources"

    def get_target(self, target_factory):
        return target_factory.python_module_imported_by_module_name(self._module_name)

    def make_resource_list(self, target):
        return target.own_resources
