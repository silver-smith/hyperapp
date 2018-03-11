from .command_class import BoundCommand, UnboundCommand
from .command import command


class BoundModeCommand(BoundCommand):

    def __init__(self, id, kind, resource_id, enabled, class_method, inst_wr, mode):
        super().__init__(id, kind, resource_id, enabled, class_method, inst_wr)
        self.mode = mode


class UnboundModeCommand(UnboundCommand):

    def __init__(self, id, kind, resource_id, enabled, class_method, mode):
        super().__init__(id, kind, resource_id, enabled, class_method)
        self._mode = mode

    def _bind(self, inst_wr, kind):
        return BoundModeCommand(self.id, kind, self._resource_id, self.enabled, self._class_method, inst_wr, self._mode)


class mode_command(command):

    def __init__(self, id, mode, kind=None, enabled=True):
        super().__init__(id, kind, enabled)
        self.mode = mode

    def instantiate(self, wrapped_class_method, resource_id):
        return UnboundModeCommand(self.id, self.kind, resource_id, self.enabled, wrapped_class_method, self.mode)
