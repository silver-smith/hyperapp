from .code.service_target import ServiceCompleteTarget


class TargetSet:

    def __init__(self, targets):
        self._name_to_target = {
            target.name: target
            for target in targets
            }

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
        return TargetFactory(self._name_to_target)


class TargetFactory:

    def __init__(self, name_to_target):
        self._name_to_target = name_to_target

    def service_complete(self, service_name):
        target = ServiceCompleteTarget(service_name)
        try:
            return self._name_to_target[target.name]
        except KeyError:
            self._name_to_target[target.name] = target
            return target
