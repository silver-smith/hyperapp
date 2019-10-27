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

    def set_commands(self, kind, command_list):
        self._kind_to_command_list[kind] = command_list
        for observer in self._observer_set:
            _log.info("Updating command (calling commands_changing) on %r: %r %r", observer, kind, command_list)
            observer.commands_changed(kind, command_list)

    def get_commands(self, kind):
        return self._kind_to_command_list.get(kind, [])
