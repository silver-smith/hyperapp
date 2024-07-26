from .code.rc_target import Target


class ConfigItemCompleteTarget(Target):

    @staticmethod
    def target_name(service_name, key):
        return f'item-complete/{service_name}/{key}'

    def __init__(self, service_name, key):
        self._service_name = service_name
        self._key = key
        self._completed = True

    @property
    def name(self):
        return self.target_name(self._service_name, self._key)

    @property
    def completed(self):
        return self._completed
