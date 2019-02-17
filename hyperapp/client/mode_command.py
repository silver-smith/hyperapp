from .commander import BoundCommand, UnboundCommand
from .command import command


class BoundModeCommand(BoundCommand):

    def __init__(self, id, kind, resource_key, enabled, class_method, inst_wr, mode):
        super().__init__(id, kind, resource_key, enabled, class_method, inst_wr)
        self.mode = mode


class UnboundModeCommand(UnboundCommand):

    def __init__(self, id, kind, resource_key, enabled, class_method, mode):
        super().__init__(id, kind, resource_key, enabled, class_method)
        self._mode = mode

    def _bind(self, inst_wr, kind):
        return BoundModeCommand(self.id, kind, self._resource_key, self.enabled, self._class_method, inst_wr, self._mode)


class mode_command(command):

    def __init__(self, id, mode, kind=None, enabled=True):
        super().__init__(id, kind, enabled)
        self.mode = mode

    def instantiate(self, wrapped_class_method, resource_key):
        return UnboundModeCommand(self.id, self.kind, resource_key, self.enabled, wrapped_class_method, self.mode)
