from dataclasses import dataclass

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_requirement import Requirement
from .code.rc_resource import Resource
from .code.config_item_resource import ConfigItemResource
from .code.python_module_resource_target import PythonModuleResourceTarget


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
        try:
            return target_factory.python_module_imported_by_code_name(self.code_name)
        except KeyError:
            target = target_factory.python_module_resource_by_code_name(self.code_name)
            assert target.is_manual
            return target

    @property
    def is_test_requirement(self):
        return True

    def update_tested_target(self, import_tgt, test_target, target_set):
        tested_resource_tgt = target_set.factory.python_module_resource_by_code_name(self.code_name)
        if not tested_resource_tgt.is_manual:
            tested_resource_tgt.add_test(test_target, target_set)

    def make_resource_list(self, target):
        if isinstance(target, PythonModuleResourceTarget):
            module_piece = target.python_module_piece
            resources = []
        else:
            module_name, recorder_piece, module_piece = target.recorded_python_module
            recorder_res = RecorderResource(
                recorder_module_name=module_name,
                recorder_piece=recorder_piece,
                )
            mark_module_item = htypes.ctr_collector.mark_module_cfg_item(
                module=mosaic.put(module_piece),
                name=module_name,
                )
            module_marker = ConfigItemResource(
                service_name='ctr_collector',
                template_ref=mosaic.put(mark_module_item),
                )
            resources = [*target.test_resources, recorder_res, module_marker]
        tested_code_res = TestedCodeResource(
            import_name=self.import_path,
            module_piece=module_piece,
            )
        return [*resources, tested_code_res]


@dataclass(frozen=True, unsafe_hash=True)
class FixturesModuleReq(Requirement):

    import_path: tuple[str]
    code_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.import_path, piece.code_name)

    @property
    def piece(self):
        return htypes.test_target.fixtures_module_req(self.import_path, self.code_name)

    def get_target(self, target_factory):
        return target_factory.python_module_imported_by_code_name(self.code_name)

    @property
    def is_test_requirement(self):
        return True

    def update_tested_target(self, import_tgt, test_target, target_set):
        test_target.add_fixtures_import(import_tgt)
        target_set.update_deps_for(test_target)

    def make_resource_list(self, target):
        return target.test_resources


class TestedCodeResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            import_name=piece.import_name,
            module_piece=web.summon(piece.module),
            )

    def __init__(self, import_name, module_piece):
        self._import_name = import_name
        self._module_piece = module_piece

    @property
    def piece(self):
        return htypes.test_target.tested_code_resource(
            import_name=tuple(self._import_name),
            module=mosaic.put(self._module_piece),
            )

    @property
    def import_records(self):
        return [htypes.builtin.import_rec(
            full_name='.'.join(self._import_name),
            resource=mosaic.put(self._module_piece),
            )]


class RecorderResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            recorder_module_name=piece.recorder_module_name,
            recorder_piece=web.summon(piece.recorder),
            )

    def __init__(self, recorder_module_name, recorder_piece):
        self._recorder_module_name = recorder_module_name
        self._recorder_piece = recorder_piece

    @property
    def piece(self):
        return htypes.test_target.recorder_resource(
            recorder_module_name=self._recorder_module_name,
            recorder=mosaic.put(self._recorder_piece),
            )

    @property
    def recorders(self):
        return {
            self._recorder_module_name: pyobj_creg.animate(self._recorder_piece),
            }
