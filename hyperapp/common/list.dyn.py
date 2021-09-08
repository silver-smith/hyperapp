from hyperapp.common.htypes import TRecord

from . import htypes


def row_t_to_column_list(types, row_t):
    assert isinstance(row_t, TRecord)
    return [
        htypes.service.column(name, types.reverse_resolve(t))
        for name, t in row_t.fields.items()
        ]
