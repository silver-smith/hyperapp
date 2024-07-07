from .code.service_target import ServiceCompleteTarget


class TargetSet:

    def __init__(self, targets):
        self._target_set = set(targets)

    def iter_ready(self):
        for target in self._target_set:
            if target.ready:
                yield target

    @property
    def all_completed(self):
        return all(t.completed for t in self._target_set)

    @property
    def count(self):
        return len(self._target_set)

    @property
    def factory(self):
        return TargetFactory(self)


class TargetFactory:

    def __init__(self, target_set):
        self._target_set = target_set

    def service_complete(self, service_name):
        return ServiceCompleteTarget(service_name)
