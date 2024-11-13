from collections import defaultdict
from operator import attrgetter

from .code.import_target import AllImportsKnownTarget, ImportTarget
from .code.python_module_resource_target import PythonModuleResourceTarget
from .code.builtin_service_target import BuiltinServiceTarget
from .code.config_item_target import ConfigItemReadyTarget, ConfigItemResolvedTarget, ConfigItemCompleteTarget
from .code.config_resource_target import ConfigResourceTarget


class TargetSet:

    def __init__(self, resource_dir, python_module_src_list):
        self._resource_dir = resource_dir
        self._stem_to_python_module_src = {
            src.stem: src
            for src in python_module_src_list
            }
        self._name_to_python_module_src = {
            src.name: src
            for src in python_module_src_list
            }
        self._name_to_target = {}
        self._dep_to_target = defaultdict(set)  # target -> target set

    def __iter__(self):
        return iter(sorted(self._name_to_target.values(), key=attrgetter('name')))

    def __getitem__(self, name):
        return self._name_to_target[name]

    @property
    def count(self):
        return len(self._name_to_target)

    def iter_ready(self):
        for target in self._name_to_target.values():
            if target.ready:
                yield target

    def iter_completed(self):
        for target in self._name_to_target.values():
            if target.completed:
                yield target

    def check_statuses(self):
        for target in self._name_to_target.values():
            for dep in target.deps:
                assert target in self._dep_to_target[dep], (target, dep)
        for target in self._name_to_target.values():
            if target.completed:
                continue
            target.update_status()
            assert not target.completed, target

    def add(self, target):
        assert target.name not in self._name_to_target
        self._name_to_target[target.name] = target
        target.update_status()
        self.update_deps_for(target)

    def update_deps_for(self, target):
        for dep_target in target.deps:
            self._dep_to_target[dep_target].add(target)

    def add_or_get(self, target):
        try:
            return self._name_to_target[target.name]
        except KeyError:
            self.add(target)
            return target

    def update_deps_statuses(self, completed_target):
        while True:
            changed_targets = set()
            for target in self._dep_to_target[completed_target]:
                prev_deps = set(target.deps)
                try:
                    target.update_status()
                except Exception as x:
                    raise RuntimeError(f"For {target.name}: {x}") from x
                new_deps = set(target.deps)
                if new_deps != prev_deps:
                    changed_targets.add(target)
            if not changed_targets:
                break
            for target in changed_targets:
                self.update_deps_for(target)

    @property
    def all_completed(self):
        return all(t.completed for t in self._name_to_target.values())

    @property
    def completed_python_module_resources(self):
        return [
            tgt for tgt in self._name_to_target.values()
            if isinstance(tgt, PythonModuleResourceTarget) and tgt.completed
            ]

    @property
    def count(self):
        return len(self._name_to_target)

    @property
    def factory(self):
        return TargetFactory(self)


class TargetFactory:

    def __init__(self, target_set):
        self._target_set = target_set

    def builtin_service(self, service_name):
        target_name = BuiltinServiceTarget.target_name_for_service_name(service_name)
        try:
            return self._target_set[target_name]
        except KeyError:
            pass
        target = BuiltinServiceTarget(service_name)
        self._target_set.add(target)
        return target

    def python_module_resource_by_code_name(self, code_name):
        src = self._target_set._stem_to_python_module_src[code_name]
        return self.python_module_resource_by_src(src)

    def python_module_resource_by_module_name(self, module_name):
        src = self._target_set._name_to_python_module_src[module_name]
        return self.python_module_resource_by_src(src)

    def python_module_resource_by_src(self, src):
        target_name = PythonModuleResourceTarget.target_name_for_src(src)
        try:
            return self._target_set[target_name]
        except KeyError:
            pass
        import_target = self.python_module_imported_by_src(src)
        target = import_target.create_resource_target(self._target_set._resource_dir)
        return self._target_set.add_or_get(target)

    def all_imports_known(self):
        return self._target_set[AllImportsKnownTarget.name]

    def python_module_imported_by_src(self, src):
        target_name = ImportTarget.name_for_src(src)
        return self._target_set[target_name]

    def python_module_imported_by_code_name(self, code_name):
        src = self._target_set._stem_to_python_module_src[code_name]
        return self.python_module_imported_by_src(src)

    def config_item_ready(self, service_name, key):
        target_name = ConfigItemReadyTarget.target_name(service_name, key)
        try:
            return self._target_set[target_name]
        except KeyError:
            pass
        all_imports_known_tgt = self.all_imports_known()
        target = ConfigItemReadyTarget(service_name, key, all_imports_known_tgt)
        self._target_set.add(target)
        return target

    def config_item_resolved(self, service_name, key):
        target_name = ConfigItemResolvedTarget.target_name(service_name, key)
        try:
            return self._target_set[target_name]
        except KeyError:
            pass
        ready_tgt = self.config_item_ready(service_name, key)
        target = ConfigItemResolvedTarget(service_name, key, ready_tgt)
        self._target_set.add(target)
        return target

    def config_item_complete(self, service_name, key):
        target_name = ConfigItemCompleteTarget.target_name(service_name, key)
        try:
            return self._target_set[target_name]
        except KeyError:
            pass
        if service_name == 'system':
            service_cfg_item_complete_tgt = None
        elif service_name in {'config_ctl_creg', 'cfg_item_creg'}:
            # Builtin services do not have matching targets. They are ready by definition.
            service_cfg_item_complete_tgt = None
        else:
            # Configuration item requires it's service to be complete because it uses it's config_ctl.
            service_cfg_item_complete_tgt = self.config_item_complete('system', service_name)
        resolved_tgt = self.config_item_resolved(service_name, key)
        target = ConfigItemCompleteTarget(service_name, key, resolved_tgt, service_cfg_item_complete_tgt)
        self._target_set.add(target)
        config_tgt = self.config_resource()
        config_tgt.add_item(service_name, target)
        return target

    def config_resource(self):
        target_name = ConfigResourceTarget.target_name()
        return self._target_set[target_name]
