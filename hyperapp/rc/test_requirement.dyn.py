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
from .code.python_module_resource_target import PythonModuleReq, PythonModuleResourceTarget


@dataclass(frozen=True)
class TestedCodeReq(Requirement):

    test_module_name: str
    import_path: tuple[str]
    code_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(
            test_module_name=piece.test_module_name,
            import_path=piece.import_path,
            code_name=piece.code_name,
            )

    @property
    def desc(self):
        return f"{self.code_name} tested code"

    @property
    def piece(self):
        return htypes.test_target.tested_code_req(
            test_module_name=self.test_module_name,
            import_path=self.import_path,
            code_name=self.code_name,
            )

    def get_target(self, target_factory):
        try:
            return target_factory.pick_module_imported_by_code_name(self.code_name)
        except KeyError:
            target = target_factory.pick_python_module_resource_by_code_name(self.code_name)
            assert target.is_manual
            return target

    @property
    def is_test_requirement(self):
        return True

    def apply_tests_import(self, import_tgt, target_set):
        tested_resource_tgt = target_set.factory.pick_python_module_resource_by_code_name(self.code_name)
        if not tested_resource_tgt.is_manual:
            tested_resource_tgt.add_tests_import(import_tgt, target_set)

    def apply_test_target(self, target, test_target, target_set):
        tested_resource_tgt = target_set.factory.pick_python_module_resource_by_code_name(self.code_name)
        if not tested_resource_tgt.is_manual:
            tested_resource_tgt.add_test(test_target, target_set)

    def make_resource_list(self, target):
        if isinstance(target, PythonModuleResourceTarget):
            module_name = target.module_name
            module_piece = target.python_module_piece
            resources = []
        else:
            module_name, recorder_piece, module_piece = target.recorded_python_module(tag='test')
            recorder_res = RecorderResource(
                recorder_module_name=module_name,
                recorder_piece=recorder_piece,
                )
            mark_module_template = htypes.ctr_collector.mark_module_template(
                name=module_name,
                )
            mark_module_cfg_item = htypes.cfg_item.data_cfg_item(
                key=mosaic.put(module_piece),
                value=mosaic.put(mark_module_template),
                )
            module_marker = ConfigItemResource(
                service_name='ctr_collector',
                cfg_item_ref=mosaic.put(mark_module_cfg_item),
                )
            resources = [*target.test_resources, recorder_res, module_marker]
        tested_code_res = TestedCodeResource(
            test_module_name=self.test_module_name,
            tested_module_name=module_name,
            import_name=self.import_path,
            module_piece=module_piece,
            )
        return [*resources, tested_code_res]

    def tested_modules(self, target_set):
        tested_target_set, module_name = target_set.find_by_name(self.code_name)
        # TODO: Include tested target set (project).
        return {module_name}


@dataclass(frozen=True)
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
        return target_factory.pick_module_imported_by_code_name(self.code_name)

    @property
    def is_test_requirement(self):
        return True

    def apply_test_target(self, target, test_target, target_set):
        test_target.add_fixtures_import(target)

    def make_resource_list(self, target):
        return target.test_resources


class TestedCodeResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            test_module_name=piece.test_module_name,
            tested_module_name=piece.tested_module_name,
            import_name=piece.import_name,
            module_piece=web.summon(piece.module),
            )

    def __init__(self, test_module_name, tested_module_name, import_name, module_piece):
        self._test_module_name = test_module_name
        self._tested_module_name = tested_module_name
        self._import_name = import_name
        self._module_piece = module_piece

    def __eq__(self, rhs):
        return (
            self.__class__ is rhs.__class__
            and self._test_module_name == rhs._test_module_name
            and self._tested_module_name == rhs._tested_module_name
            and self._import_name == rhs._import_name
            and self._module_piece == rhs._module_piece
            )

    def __hash__(self):
        return hash((
            'tested-code-resource',
            self._test_module_name,
            self._tested_module_name,
            self._import_name,
            self._module_piece,
            ))

    @property
    def piece(self):
        return htypes.test_target.tested_code_resource(
            test_module_name=self._test_module_name,
            tested_module_name=self._tested_module_name,
            import_name=tuple(self._import_name),
            module=mosaic.put(self._module_piece),
            )

    @property
    def system_config_items(self):
        template = htypes.import_resource.import_template(
            import_name=self._import_name,
            resource=mosaic.put(self._module_piece),
            )
        cfg_item = htypes.import_resource.import_key_cfg_item(
            module_name=self._test_module_name,
            import_name=self._import_name,
            value=mosaic.put(template),
            )
        return {'import_recorder_reg': [cfg_item]}

    @property
    def tested_modules(self):
        return [self._tested_module_name]


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

    def __eq__(self, rhs):
        return (
            self.__class__ is rhs.__class__
            and self._recorder_module_name == rhs._recorder_module_name
            and self._recorder_piece == rhs._recorder_piece
            )

    def __hash__(self):
        return hash(('recorder-resource', self._recorder_module_name, self._recorder_piece))

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
