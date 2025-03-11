from . import htypes
from .services import (
    pyobj_creg,
    )
from .tested.code import column_format


def test_format():
    piece = htypes.column.column_k(
        model_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        column_name='sample_column',
        )
    title = column_format.format_column(piece)
    assert title == "column_k(builtin.string:sample_column)"
