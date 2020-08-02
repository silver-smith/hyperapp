import logging
import operator
import weakref

_log = logging.getLogger(__name__)


class CommandHub:

    def __init__(self, get_commands=None):
        self._get_commands = get_commands
        self._observer_set = weakref.WeakSet()

    def init_get_commands(self, get_commands):
        self._get_commands = get_commands

    def subscribe(self, observer):
        self._observer_set.add(observer)

    def unsubscribe(self, observer):
        self._observer_set.remove(observer)

    def update(self, only_kind=None):
        _log.info("Update commands (only_kind=%s)", only_kind)
        all_command_list = self._get_commands()
        if only_kind:
            kind_list = [only_kind]
        else:
            kind_list = ['view', 'global', 'object', 'element']
        for kind in kind_list:
            command_list = [command for command in all_command_list if command.kind == kind]
            for observer in self._observer_set:
                _log.info("Updating commands (calling commands_changing) on %r: %r %r", observer, kind, [command.id for command in command_list])
                observer.commands_changed(kind, command_list)
