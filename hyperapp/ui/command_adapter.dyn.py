import logging
from functools import cached_property

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class ObjectCommandAdapter:

    @classmethod
    async def from_piece(cls, impl, object_piece, navigator, adapter, view, python_object_creg):
        dir = python_object_creg.invite(impl.dir)
        fn = getattr(adapter.object, impl.method, impl.params)
        return cls(dir, fn, navigator, view, impl.params)

    def __init__(self, dir, fn, navigator, view, params):
        self._dir = dir
        self._fn = fn
        self._navigator = navigator
        self._view = view
        self._params = params

    @property
    def dir(self):
        return self._dir

    @property
    def name(self):
        return self._dir._t.name.rstrip('_d')  # todo: remove name from commands.

    @property
    def kind(self):
        return 'object'

    async def run(self):
        view_state = self._view.state
        log.info("Run object command: %s with state %s", self._dir, view_state)
        kw = {
            name: getattr(view_state, name)
            for name in self._params
            }
        result = self._fn(**kw)
        log.info("Run object command %s result: %r", self._dir, result)
        if result:
            await self._navigator.save_history_and_open_piece(result, self._dir)
    

class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.command_registry.register_actor(
            htypes.impl.object_command_impl, ObjectCommandAdapter.from_piece, services.python_object_creg)
