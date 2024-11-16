from collections import defaultdict
from operator import attrgetter

from .code.import_target import AllImportsKnownTarget, ImportTarget
from .code.python_module_resource_target import PythonModuleResourceTarget
from .code.builtin_service_target import BuiltinServiceTarget
from .code.config_item_target import ConfigItemReadyTarget, ConfigItemResolvedTarget, ConfigItemCompleteTarget
from .code.config_resource_target import ConfigResourceTarget
from .code.service_req import ServiceReq


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
        self._prev_completed = set()
        self._prev_incomplete_deps_map = {}

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

    def add(self, target):
        assert target.name not in self._name_to_target
        self._name_to_target[target.name] = target

    def add_or_get(self, target):
        try:
            return self._name_to_target[target.name]
        except KeyError:
            self.add(target)
            return target

    @property
    def _completed_targets(self):
        return set(self.iter_completed())

    @property
    @staticmethod
    def _reverse_deps_map(self):
        dep_to_targets = defaultdict(set)  # target -> target set
        for target in self._name_to_target.values():
            for dep in target.deps:
                dep_to_targets[dep].add(target)
        return dict(dep_to_targets)

    # Only for completed targets.
    @property
    @staticmethod
    def _incomplete_deps_map(self):
        return {
            target: target.deps
            for target in self._name_to_target.values()
            if not target.completed
            }

    @staticmethod
    def _update_target(target):
        try:
            target.update_status()
        except Exception as x:
            raise RuntimeError(f"For {target.name}: {x}") from x

    def _update_dependent(self, target_set):
        dep_to_targets = self._reverse_deps_map
        for completed_target in target_set:
            for dep_target in dep_to_targets.get(completed_target, []):
                self._update_target(dep_target)

    def _update_new_or_with_changed_deps(self):
        for target in [*self._name_to_target.values()]:
            if target.completed:
                continue
            try:
                prev_deps = self._prev_incomplete_deps_map[target]
            except KeyError:
                pass  # New target was added. Update it.
            else:
                if target.deps == prev_deps:
                    continue
            # It's deps were changed or it was just added.
            self._update_target(target)

    # After updating a target:
    # * Deps for it any other target may change;
    # * It or any other target may become completed;
    # * New targets may be added in completed or incomplete state.
    # Outside of update_statuses call:
    # * Any target may become completed.
    # * Any target may have it's deps changed.
    def update_statuses(self):
        while True:
            completed_targets = self._completed_targets
            assert completed_targets >= self._prev_completed  # Demotions are not allowed.
            new_completed = completed_targets - self._prev_completed
            if not new_completed:
                break
            self._update_dependent(new_completed)
            self._update_new_or_with_changed_deps()
            self._prev_completed = completed_targets
            self._prev_incomplete_deps_map = self._incomplete_deps_map

    def init_all_statuses(self):
        self._prev_incomplete_deps_map = self._incomplete_deps_map
        for target in [*self._name_to_target.values()]:
            self._update_target(target)

    def check_statuses(self):
        for target in self._name_to_target.values():
            if target.completed:
                continue
            deps = target.deps
            target.update_status()
            assert not target.completed, target
            assert target.deps == deps

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
        target = ConfigItemReadyTarget(self._target_set, service_name, key, all_imports_known_tgt)
        self._target_set.add(target)
        return target

    def config_item_resolved(self, service_name, key):
        target_name = ConfigItemResolvedTarget.target_name(service_name, key)
        try:
            return self._target_set[target_name]
        except KeyError:
            pass
        ready_tgt = self.config_item_ready(service_name, key)
        target = ConfigItemResolvedTarget(self._target_set, service_name, key, ready_tgt)
        self._target_set.add(target)
        return target

    def config_item_complete(self, service_name, key, req=None):
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
            service_cfg_item_complete_tgt = self.config_item_complete('system', service_name, ServiceReq(service_name))
        resolved_tgt = self.config_item_resolved(service_name, key)
        target = ConfigItemCompleteTarget(self._target_set, service_name, key, resolved_tgt, service_cfg_item_complete_tgt)
        self._target_set.add(target)
        config_tgt = self.config_resource()
        config_tgt.add_item(service_name, target, req)
        return target

    def config_resource(self):
        target_name = ConfigResourceTarget.target_name()
        return self._target_set[target_name]
