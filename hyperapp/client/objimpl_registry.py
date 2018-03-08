# object implementaion registry

import inspect
import logging
from .registry import Registry

log = logging.getLogger(__name__)


class ObjImplRegistry(Registry):

    def __init__(self, produce_name):
        super().__init__()
        self._produce_name = produce_name

    async def resolve(self, state, *args):
        rec = self._resolve(state.objimpl_id)
        log.info('producing %s %r using %s(%s + %s, %s)', self._produce_name, state.objimpl_id, rec.factory, args, rec.args, rec.kw)
        return (await self._run_awaitable_factory(rec.factory, state, *(args + rec.args), **rec.kw))
