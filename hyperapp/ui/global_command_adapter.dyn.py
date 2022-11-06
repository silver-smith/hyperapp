import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class GlobalCommandAdapter:

    @classmethod
    async def from_piece(cls, impl, navigator, object_piece, adapter, view, web, python_object_creg):
        fn = python_object_creg.invite(impl.function)
        dir = web.summon(impl.dir)
        return cls(dir, fn, navigator, view)

    def __init__(self, dir, fn, navigator, view):
        self._dir = dir
        self._fn = fn
        self._navigator = navigator
        self._view = view

    @property
    def dir(self):
        return self._dir

    @property
    def name(self):
        return self._dir._t.name.rstrip('_d')  # todo: remove name from commands.

    @property
    def kind(self):
        return 'global'

    async def run(self):
        log.info("Run global command: %s", self._dir)
        result = self._fn()
        log.info("Run global command %s result: %r", self._dir, result)
        if result:
            await self._navigator.save_history_and_open_piece(result, self._dir)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.command_registry.register_actor(
            htypes.impl.global_command_impl, GlobalCommandAdapter.from_piece, services.web, services.python_object_creg)
