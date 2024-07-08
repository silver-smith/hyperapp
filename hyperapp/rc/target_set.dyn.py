from collections import defaultdict
from operator import attrgetter

from .code.import_target import ImportTargetAlias
from .code.python_module_resource_target import PythonModuleResourceTarget
from .code.service_target import ServiceFoundTarget, ServiceCompleteTarget


class TargetSet:

    def __init__(self, python_module_src_list, targets):
        self._stem_to_python_module_src = {
            src.stem: src
            for src in python_module_src_list
            }
        self._name_to_target = {}
        self._dep_to_target = defaultdict(set)  # target -> target set
        for tgt in targets:
            self.add(tgt)

    def __iter__(self):
        return iter(sorted(self._name_to_target.values(), key=attrgetter('name')))

    def iter_ready(self):
        for target in self._name_to_target.values():
            if target.ready:
                yield target

    def add(self, target):
        self._name_to_target[target.name] = target
        for dep_target in target.deps:
            self._dep_to_target[dep_target].add(target)

    def add_or_get(self, target):
        try:
            return self._name_to_target[target.name]
        except KeyError:
            self.add(target)
            return target

    def update_deps_statuses(self, completed_target):
        for target in self._dep_to_target[completed_target]:
            target.update_status()

    @property
    def all_completed(self):
        return all(t.completed for t in self._name_to_target.values())

    @property
    def count(self):
        return len(self._name_to_target)

    @property
    def factory(self):
        return TargetFactory(self)


class TargetFactory:

    def __init__(self, target_set):
        self._target_set = target_set

    def service_complete(self, service_name):
        target = ServiceCompleteTarget(service_name)
        return self._target_set.add_or_get(target)

    def python_module_resource(self, code_name):
        src = self._target_set._stem_to_python_module_src[code_name]
        target = PythonModuleResourceTarget(src)
        return self._target_set.add_or_get(target)

    def tested_service(self, service_name):
        target = ServiceFoundTarget(service_name)
        return self._target_set.add_or_get(target)

    def tested_code(self, code_name):
        src = self._target_set._stem_to_python_module_src[code_name]
        target = ImportTargetAlias(src)
        return self._target_set.add_or_get(target)
