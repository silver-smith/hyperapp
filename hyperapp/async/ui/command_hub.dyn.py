import logging
import operator
import weakref
from functools import partial

from hyperapp.common.module import Module

_log = logging.getLogger(__name__)


class CommandHubList:

    def __init__(self):
        self._hubs = weakref.WeakSet()

    def add(self, hub):
        self._hubs.add(hub)

    async def update(self, only_kind=None):
        _log.info("Update commands (only_kind=%s) for all hubs", only_kind)
        for hub in self._hubs:
            await hub.update(only_kind)


class CommandHub:

    def __init__(self, hub_list):
        self._observer_set = weakref.WeakSet()
        self._get_commands = None
        hub_list.add(self)

    async def init_get_commands(self, get_commands):
        self._get_commands = get_commands
        await self.update()

    def subscribe(self, observer):
        self._observer_set.add(observer)

    def unsubscribe(self, observer):
        self._observer_set.remove(observer)

    async def update(self, only_kind=None):
        _log.info("Update commands (only_kind=%s)", only_kind)
        all_command_list = await self._get_commands()
        if only_kind:
            kind_list = [only_kind]
        else:
            kind_list = ['view', 'global', 'object', 'element']
        for kind in kind_list:
            command_list = [command for command in all_command_list if command.kind == kind]
            for observer in self._observer_set:
                _log.info("Updating commands (calling commands_changing) on %r: %r %r", observer, kind, [command.name for command in command_list])
                observer.commands_changed(kind, command_list)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.command_hub_list = hub_list = CommandHubList()
        services.command_hub_factory = partial(CommandHub, hub_list)
