# object implementaion registry

import inspect
import logging
from .registry import Registry

log = logging.getLogger(__name__)


class ObjImplRegistry(Registry):

    async def resolve(self, state):
        rec = self._resolve(state.objimpl_id)
        log.info('producing object %r using %s(%s, %s)', state.objimpl_id, rec.factory, rec.args, rec.kw)
        result = rec.factory(state, *rec.args, **rec.kw)
        if inspect.isawaitable(result):
            return (await result)
        else:
            return result
