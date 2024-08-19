from . import htypes
from .services import (
    mosaic,
    web,
    )


class Constructor:

    @property
    def is_fixture(self):
        return False

    def update_resource_targets(self, resource_tgt, target_set):
        pass

    def update_fixtures_targets(self, import_alias_tgt, target_set):
        pass

    def update_targets(self, target_set):
        pass

    def make_component(self, python_module, name_to_res=None):
        raise NotImplementedError(self)

    def get_component(self, name_to_res):
        raise NotImplementedError(self)

    def make_resource(self, module_name, python_module):
        pass


class ModuleWrapperCtr(Constructor):

    @classmethod
    def from_piece(cls, piece, rc_constructor_creg):
        return cls(
            module_name=piece.module_name,
            constructor=rc_constructor_creg.invite(piece.constructor),
            )

    def __init__(self, module_name, constructor):
        self._module_name = module_name
        self._constructor = constructor

    @property
    def piece(self):
        return htypes.rc_constructors.module_wrapper(
            module_name=self._module_name,
            constructor=mosaic.put(self._constructor.piece),
            )

    def update_targets(self, target_set):
        resource_tgt = target_set.factory.python_module_resource_by_module_name(self._module_name)
        self._constructor.update_resource_targets(resource_tgt, target_set)
