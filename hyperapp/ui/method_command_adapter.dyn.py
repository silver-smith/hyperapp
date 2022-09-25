import inspect
import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class MethodCommandAdapter:

    @classmethod
    async def from_piece(cls, impl, navigator, object_piece, adapter, view, python_object_creg):
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
        kw = {}
        for name in self._params:
            if name == 'current_item':
                value = self._view.current_item
            else:
                value = getattr(view_state, name)
            kw[name] = value
        log.info("Run object command: %s with params %s", self._dir, kw)
        result = self._fn(**kw)
        if inspect.iscoroutine(result):
            result = await result
        log.info("Run object command %s result: %r", self._dir, result)
        if result:
            await self._navigator.save_history_and_open_piece(result, self._dir)
    

class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.command_registry.register_actor(
            htypes.impl.method_command_impl, MethodCommandAdapter.from_piece, services.python_object_creg)
