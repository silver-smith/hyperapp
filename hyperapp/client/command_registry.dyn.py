import logging
import weakref

_log = logging.getLogger(__name__)


class CommandRegistry:

    def __init__(self):
        self._observer_set = weakref.WeakSet()
        self._kind_to_command_list = {}

    def subscribe(self, observer):
        self._observer_set.add(observer)

    def unsubscribe(self, observer):
        self._observer_set.remove(observer)

    def set_kind_commands(self, kind, command_list):
        self._kind_to_command_list[kind] = command_list
        for observer in self._observer_set:
            _log.info("Updating command (calling commands_changing) on %r: %r %r", observer, kind, command_list)
            observer.commands_changed(kind, command_list)

    def get_kind_commands(self, kind):
        return self._kind_to_command_list.get(kind, [])

    def set_commands_from_registry(self, command_registry):
        _log.info("Updating all command from registry")
        self._kind_to_command_list = {**command_registry._kind_to_command_list}
        for observer in self._observer_set:
            for kind in ['global', 'view', 'object']:
                command_list = self._kind_to_command_list.get(kind, [])
                _log.info("Updating command (calling commands_changing) on %r: %r %r", observer, kind, command_list)
                observer.commands_changed(kind, command_list)
