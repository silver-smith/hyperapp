# object implementaion registry

import inspect
import logging
from hyperapp.common.registry import Registry
from hyperapp.common.module import Module
from hyperapp.client.async_registry import run_awaitable_factory

log = logging.getLogger(__name__)


MODULE_NAME = 'objimpl_registry'


class ObjImplRegistry(Registry):

    def __init__(self, produce_name):
        super().__init__()
        self._produce_name = produce_name

    async def resolve_async(self, state, *args, **kw):
        rec = self._resolve(state.impl_id)
        log.info('Producing %s %r using %s(%s + %s, %s)', self._produce_name, state.impl_id, rec.factory, args, rec.args, rec.kw)
        return (await run_awaitable_factory(rec.factory, state, *(args + rec.args), **dict(rec.kw, **kw)))


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.objimpl_registry = ObjImplRegistry('object')
