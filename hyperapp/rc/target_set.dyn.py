from .code.service_target import ServiceCompleteTarget


class TargetSet:

    def __init__(self):
        self._target_set = set()

    @property
    def all_ready(self):
        for target in self._target_set:
            if target.ready:
                yield target

    @property
    def factory(self):
        return TargetFactory(self)


class TargetFactory:

    def __init__(self, target_set):
        self._target_set = target_set

    def service_complete(self, service_name):
        return ServiceCompleteTarget(service_name)
