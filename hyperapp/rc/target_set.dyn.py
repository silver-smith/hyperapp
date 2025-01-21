from collections import defaultdict
from operator import attrgetter

from .code.import_target import AllImportsKnownTarget, ImportTarget
from .code.python_module_resource_target import PythonModuleResourceTarget
from .code.builtin_service_target import BuiltinServiceTarget
from .code.config_item_target import ConfigItemReadyTarget, ConfigItemResolvedTarget, ConfigItemCompleteTarget
from .code.config_resource_target import ConfigResourceTarget
from .code.service_req import ServiceReq
from .code.type_target import TypeTarget


def _sorted_targets(targets):
    return sorted(targets, key=attrgetter('name'))


class GlobalTargets:

    def __init__(self):
        self._name_to_target = {}

    def __getitem__(self, name):
        return self._name_to_target[name]

    def add(self, target):
        assert target.name not in self._name_to_target
        self._name_to_target[target.name] = target


class TargetSet:

    def __init__(self, globals_targets, resource_dir, types, imports):
        self._globals_targets = globals_targets
        self._resource_dir = resource_dir
        self._imports = imports  # TargetSet set.
        self._types = types
        self._name_to_full_name = {}
        self._full_name_to_name = {}
        self._name_to_target = {}
        self._prev_completed = set()
        self._prev_incomplete_deps_map = {}

    def __iter__(self):
        return iter(_sorted_targets(self._name_to_target.values()))

    def __getitem__(self, name):
        return self._name_to_target[name]

    @property
    def globals(self):
        return self._globals_targets

    @property
    def count(self):
        return len(self._name_to_target)

    def iter_ready(self):
        for target in self:
            if target.ready:
                yield target

    def iter_completed(self):
        for target in self:
            if target.completed:
                yield target

    def add_module_name(self, full_name, name):
        self._full_name_to_name[full_name] = name
        self._name_to_full_name[name] = full_name

    def add(self, target):
        assert target.name not in self._name_to_target
        self._name_to_target[target.name] = target

    def adopt(self, target):
        self.add(target)

    def full_module_name(self, name):
        return self._name_to_full_name[name]

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
        if target.completed:
            return
        try:
            target.update_status()
        except Exception as x:
            raise RuntimeError(f"For {target.name}: {x}") from x

    def _update_dependent(self, completed_target_set):
        dep_to_targets = self._reverse_deps_map
        dep_targets = set()
        for completed_target in completed_target_set:
            for target in dep_to_targets.get(completed_target, []):
                dep_targets.add(target)
        for target in _sorted_targets(dep_targets):
            self._update_target(target)

    def _enum_new_and_with_changed_deps(self, prev_dep_map, new_dep_map):
        for target, deps in new_dep_map.items():
            try:
                prev_deps = prev_dep_map[target]
            except KeyError:
                yield target  # New.
            else:
                if deps != prev_deps:
                    yield target

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
            new_deps_map = self._incomplete_deps_map
            changed_targets = _sorted_targets(
                self._enum_new_and_with_changed_deps(self._prev_incomplete_deps_map, new_deps_map))
            if not new_completed and not changed_targets:
                break
            self._update_dependent(new_completed)
            for target in changed_targets:
                self._update_target(target)
            self._prev_completed = completed_targets
            self._prev_incomplete_deps_map = new_deps_map

    def init_all_statuses(self):
        self._prev_incomplete_deps_map = self._incomplete_deps_map
        for target in [*self._name_to_target.values()]:
            self._update_target(target)

    def post_init(self):
        self.factory.all_imports_known().init_completed()
        self.init_all_statuses()
        self.update_statuses()

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
    def ready_req_to_resources(self):
        req_to_resources = {}
        for target_set in self._imports:
            req_to_resources.update(target_set.ready_req_to_resources)
        req_to_resources.update(self.factory.config_resource().ready_req_to_resources)
        return req_to_resources

    @property
    def factory(self):
        return TargetFactory(self)


class TargetFactory:

    def __init__(self, target_set):
        self._target_set = target_set

    def type(self, module_name, name):
        target_name = TypeTarget.target_name(module_name, name)
        try:
            return self._target_set[target_name]
        except KeyError:
            pass
        target = TypeTarget(self._target_set._types, module_name, name)
        self._target_set.add(target)
        return target
        
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
        full_name = self._target_set.full_module_name(code_name)
        return self.python_module_resource_by_module_name(full_name)

    def python_module_resource_by_module_name(self, module_name):
        target_name = PythonModuleResourceTarget.target_name_for_module_name(module_name)
        try:
            return self._target_set[target_name]
        except KeyError:
            pass
        import_target = self.python_module_imported_by_module_name(module_name)
        target = import_target.create_resource_target(self._target_set._resource_dir)
        self._target_set.add(target)
        return target

    def all_imports_known(self):
        return self._target_set[AllImportsKnownTarget.name]

    def python_module_imported_by_module_name(self, module_name):
        target_name = ImportTarget.name_for_module_name(module_name)
        return self._target_set[target_name]

    def python_module_imported_by_code_name(self, code_name):
        full_name = self._target_set.full_module_name(code_name)
        return self.python_module_imported_by_module_name(full_name)

    def config_item_ready(self, service_name, key):
        target_name = ConfigItemReadyTarget.target_name(service_name, key)
        try:
            return self._target_set.globals[target_name]
        except KeyError:
            pass
        all_imports_known_tgt = self.all_imports_known()
        target = ConfigItemReadyTarget(self._target_set, service_name, key, all_imports_known_tgt)
        self._target_set.globals.add(target)
        return target

    def config_item_resolved(self, service_name, key):
        target_name = ConfigItemResolvedTarget.target_name(service_name, key)
        try:
            return self._target_set.globals[target_name]
        except KeyError:
            pass
        ready_tgt = self.config_item_ready(service_name, key)
        target = ConfigItemResolvedTarget(self._target_set, service_name, key, ready_tgt)
        self._target_set.globals.add(target)
        return target

    def config_item_complete(self, service_name, key, req=None):
        target_name = ConfigItemCompleteTarget.target_name(service_name, key)
        try:
            return self._target_set.globals[target_name]
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
        self._target_set.globals.add(target)
        config_tgt = self.config_resource()
        config_tgt.add_item(service_name, target, req)
        return target

    def config_items(self, service_name, key, req=None, provider=None, ctr=None):
        ready_tgt = self.config_item_ready(service_name, key)
        resolved_tgt = self.config_item_resolved(service_name, key)
        complete_tgt = self.config_item_complete(service_name, key, req)
        if provider is not None:
            ready_tgt.set_provider(provider)
        if ctr is not None:
            resolved_tgt.resolve(ctr)
        return (ready_tgt, resolved_tgt, complete_tgt)

    def config_resource(self):
        target_name = ConfigResourceTarget.target_name()
        return self._target_set[target_name]
