import logging
from dataclasses import dataclass
from functools import cached_property

from hyperapp.common.util import flatten

from . import htypes
from .services import (
    resource_module_factory,
    )
from .code.rc_target import Target
from .code.rc_requirement import Requirement
from .code.import_resource import ImportResource

rc_log = logging.getLogger('rc')


@dataclass(frozen=True, unsafe_hash=True)
class PythonModuleReq(Requirement):

    code_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.code_name)

    @property
    def piece(self):
        return htypes.python_module_resource_target.python_module_req(self.code_name)

    def get_target(self, target_factory):
        return target_factory.python_module_resource_by_code_name(self.code_name)

    def make_resource(self, target):
        return ImportResource(['code', self.code_name], target.python_module_piece)


class PythonModuleResourceTarget(Target):

    @classmethod
    def target_name_for_src(cls, python_module_src):
        return cls.target_name_for_module_name(python_module_src.name)

    @staticmethod
    def target_name_for_module_name(module_name):
        return f'resource/{module_name}'

    def __init__(self, python_module_src):
        self._src = python_module_src

    @property
    def name(self):
        return self.target_name_for_src(self._src)

    def get_resource_component(self, ctr):
        return ctr.get_component(self._resource_module)

    @property
    def module_name(self):
        return self._src.name

    @property
    def code_name(self):
        return self._src.stem


class ManualPythonModuleResourceTarget(PythonModuleResourceTarget):

    def __init__(self, python_module_src, custom_resource_registry, resource_dir, resource_text):
        super().__init__(python_module_src)
        self._resource_module = resource_module_factory(
            custom_resource_registry, self._src.name, resource_dir=resource_dir, text=resource_text)
        custom_resource_registry.set_module(self._src.name, self._resource_module)

    @property
    def completed(self):
        return True

    @property
    def is_manual(self):
        return True

    @property
    def import_alias_tgt(self):
        return None

    @cached_property
    def python_module_piece(self):
        name = f'{self._src.stem}.module'
        return self._resource_module[name]


class CompiledPythonModuleResourceTarget(PythonModuleResourceTarget):

    def __init__(self, python_module_src, custom_resource_registry, resource_dir, types, all_imports_known_tgt, import_alias_tgt):
        super().__init__(python_module_src)
        self._types = types
        self._all_imports_known_tgt = all_imports_known_tgt
        self._import_alias_tgt = import_alias_tgt
        self._resource_module = resource_module_factory(
            custom_resource_registry, self._src.name, resource_dir=resource_dir)
        custom_resource_registry.set_module(self._src.name, self._resource_module)
        self._completed = False
        self._req_to_target = {}
        self._type_resources = set()
        self._tests = set()
        self._cfg_item_targets = set()
        self._python_module_piece = None

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {
            self._all_imports_known_tgt,
            self._import_alias_tgt,
            *self._req_to_target.values(),
            *self._cfg_item_targets,
            *self._tests,
            }

    def update_status(self):
        if self._completed:
            return
        if all(target.completed for target in self.deps):
            self._construct()
            self._completed = True

    @property
    def has_output(self):
        return True

    @property
    def is_manual(self):
        return False

    @property
    def import_alias_tgt(self):
        return self._import_alias_tgt

    def add_import_requirements(self, req_to_target):
        assert not self._completed
        self._req_to_target = req_to_target

    def add_cfg_item_target(self, target):
        assert not self._completed
        self._cfg_item_targets.add(target)

    def add_test(self, test_target, target_set):
        assert not self._completed
        self._tests.add(test_target.alias)
        test_target.add_tested_import(self._import_alias_tgt)
        target_set.update_deps_for(test_target)
        target_set.update_deps_for(self)

    def add_used_imports(self, import_list):
        assert not self._completed
        for name in import_list:
            if len(name) < 3:
                continue
            if name[0] != 'htypes':
                continue
            type_src = self._types.get_src(name[1], name[2])
            resource = ImportResource.from_type_src(type_src)
            self._type_resources.add(resource)

    @cached_property
    def python_module_piece(self):
        assert self._completed
        return self._python_module_piece

    def _enum_resources(self):
        yield from self._type_resources
        for req, target in self._req_to_target.items():
            yield from req.make_resource_list(target)

    def _construct(self):
        rc_log.debug("Construct: %s", self.name)
        resources = list(self._enum_resources())
        import_list = sorted(flatten(d.import_records for d in resources))
        python_module = self._src.python_module(import_list)
        self._resource_module[f'{self._src.stem}.module'] = python_module
        self._python_module_piece = python_module
        for item_tgt in self._cfg_item_targets:
            item_tgt.constructor.make_component(self._types, python_module, self._resource_module)

    def get_output(self):
        return (self._src.resource_path, self._resource_module.as_text)
