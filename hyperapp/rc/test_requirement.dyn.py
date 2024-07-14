from dataclasses import dataclass

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_requirement import Requirement
from .code.rc_resource import Resource


@dataclass(frozen=True, unsafe_hash=True)
class TestedServiceReq(Requirement):

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.test_target.tested_service_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.tested_service(self.service_name)

    @property
    def is_test_requirement(self):
        return True

    def make_resource(self, target):
        return None


@dataclass(frozen=True, unsafe_hash=True)
class TestedCodeReq(Requirement):

    import_path: tuple[str]
    code_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.import_path, piece.code_name)

    @property
    def piece(self):
        return htypes.test_target.tested_code_req(self.import_path, self.code_name)

    def get_target(self, target_factory):
        return target_factory.python_module_imported_by_code_name(self.code_name)

    @property
    def is_test_requirement(self):
        return True

    def get_tested_resource_target(self, target_factory):
        return target_factory.python_module_resource_by_code_name(self.code_name)

    def get_tested_import_target(self, target_factory):
        return target_factory.python_module_imported_by_code_name(self.code_name)

    def make_resource(self, target):
        recorder_module_name, recorder_piece, module_piece = target.recorded_python_module()
        return TestedCodeResource(
            import_name=self.import_path,
            module_piece=module_piece,
            recorder_module_name=recorder_module_name,
            recorder_piece=recorder_piece,
            )


class TestedCodeResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            import_name=piece.import_name,
            module_piece=web.summon(piece.module),
            recorder_module_name=piece.recorder_module_name,
            recorder_piece=web.summon(piece.recorder),
            )

    def __init__(self, import_name, module_piece, recorder_module_name, recorder_piece):
        self._import_name = import_name
        self._module_piece = module_piece
        self._recorder_module_name = recorder_module_name
        self._recorder_piece = recorder_piece

    @property
    def piece(self):
        return htypes.test_target.tested_code_resource(
            import_name=tuple(self._import_name),
            module=mosaic.put(self._module_piece),
            recorder_module_name=self._recorder_module_name,
            recorder=mosaic.put(self._recorder_piece),
            )

    @property
    def import_records(self):
        return [htypes.builtin.import_rec(
            full_name='.'.join(self._import_name),
            resource=mosaic.put(self._module_piece),
            )]

    @property
    def recorders(self):
        return {
            self._recorder_module_name: pyobj_creg.animate(self._recorder_piece),
            }
