# object implementaion registry

import inspect
import logging
from .registry import Registry

log = logging.getLogger(__name__)


class ObjImplRegistry(Registry):

    async def resolve(self, state):
        rec = self._resolve(state.objimpl_id)
        log.info('producing object %r using %s(%s, %s)', state.objimpl_id, rec.factory, rec.args, rec.kw)
        return (await self._run_awaitable_factory(rec.factory, state, *rec.args, **rec.kw))
