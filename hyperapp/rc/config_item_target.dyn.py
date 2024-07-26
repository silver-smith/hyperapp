from .code.rc_target import Target


class ConfigItemReadyTarget(Target):

    @staticmethod
    def target_name(service_name, key):
        return f'item-ready/{service_name}/{key}'

    def __init__(self, service_name, key):
        self._service_name = service_name
        self._key = key
        self._completed = False

    @property
    def name(self):
        return self.target_name(self._service_name, self._key)

    @property
    def completed(self):
        return self._completed


class ConfigItemCompleteTarget(Target):

    @staticmethod
    def target_name(service_name, key):
        return f'item-complete/{service_name}/{key}'

    def __init__(self, service_name, key, ready_tgt):
        self._service_name = service_name
        self._key = key
        self._ready_tgt = ready_tgt
        self._completed = False

    @property
    def name(self):
        return self.target_name(self._service_name, self._key)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {self._ready_tgt}
