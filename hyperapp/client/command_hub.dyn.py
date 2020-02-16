import logging
import operator
import weakref

_log = logging.getLogger(__name__)


class CommandHub:

    def __init__(self, get_commands):
        self._get_commands = get_commands
        self._observer_set = weakref.WeakSet()

    def subscribe(self, observer):
        self._observer_set.add(observer)

    def unsubscribe(self, observer):
        self._observer_set.remove(observer)

    def push_kind_commands(self, kind, command_list):
        _log.info("Push %r commands: %r", kind, [command.id for command in command_list])
        for observer in self._observer_set:
            _log.info("Updating command (calling commands_changing) on %r: %r %r", observer, kind, [command.id for command in command_list])
            observer.commands_changed(kind, command_list)

    def update(self):
        _log.info("Update commands")
        all_command_list = self._get_commands()
        for kind in ['view', 'global', 'object', 'element']:
            command_list = [command for command in all_command_list if command.kind == kind]
            for observer in self._observer_set:
                _log.info("Updating command (calling commands_changing) on %r: %r %r", observer, kind, [command.id for command in command_list])
                observer.commands_changed(kind, command_list)
