from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )


def data_to_piece(piece):
    t = deduce_t(piece)
    # TODO: Add support for other types.
    if not isinstance(t, TRecord):
        return None
    assert not t.fields  # TODO: Add support for non-empty records.
    t_ref = pyobj_creg.actor_to_ref(t)
    return htypes.builtin.call(
        function=t_ref,
        )
