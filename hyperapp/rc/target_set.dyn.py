from operator import attrgetter

from .code.python_module_resource_target import PythonModuleResourceTarget
from .code.service_target import ServiceCompleteTarget


class TargetSet:

    def __init__(self, python_module_src_list, targets):
        self._name_to_target = {
            target.name: target
            for target in targets
            }
        self._stem_to_python_module_src = {
            src.stem: src
            for src in python_module_src_list
            }

    def __iter__(self):
        return iter(sorted(self._name_to_target.values(), key=attrgetter('name')))

    def iter_ready(self):
        for target in self._name_to_target.values():
            if target.ready:
                yield target

    def add(self, target):
        self._name_to_target[target.name] = target

    @property
    def all_completed(self):
        return all(t.completed for t in self._name_to_target.values())

    @property
    def count(self):
        return len(self._name_to_target)

    @property
    def factory(self):
        return TargetFactory(self._stem_to_python_module_src, self._name_to_target)


class TargetFactory:

    def __init__(self, stem_to_python_module_src, name_to_target):
        self._stem_to_python_module_src = stem_to_python_module_src
        self._name_to_target = name_to_target

    def service_complete(self, service_name):
        target = ServiceCompleteTarget(service_name)
        try:
            return self._name_to_target[target.name]
        except KeyError:
            self._name_to_target[target.name] = target
            return target

    def python_module_resource(self, code_name):
        src = self._stem_to_python_module_src[code_name]
        return PythonModuleResourceTarget(src)
