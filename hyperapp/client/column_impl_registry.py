# list view column type implementaion registry

import logging
from .registry import Registry
from .list_column_type import ColumnType

log = logging.getLogger(__name__)


class ObjImplRegistry(Registry):

    def resolve(self, state):
        rec = self._resolve(state.impl_id)
        log.info('producing column type %r using %s(%s, %s)', state.impl_id, rec.factory, rec.args, rec.kw)
        column_type = rec.factory(state, *rec.args, **rec.kw)
        assert isinstance(column_type, ColumnType), repr((state.impl_id, column_type))  # must resolve to ColumnType
        return column_type
