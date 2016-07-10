# object implementaion registry

import logging
from .registry import Registry

log = logging.getLogger(__name__)


class ObjImplRegistry(Registry):

    def resolve( self, state, locale ):
        rec = self._resolve(state.objimpl_id)
        log.info('producing object %r using %s(%s, %s)', state.objimpl_id, rec.factory, rec.args, rec.kw)
        return rec.factory(state, locale, *rec.args, **rec.kw)
