from hyperapp.common.htypes import TRecord
from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from . import htypes
from .services import (
    deduce_t,
    mark,
    pyobj_creg,
    )


@mark.service
def data_to_res():
    def _data_to_res(piece):
        t = deduce_t(piece)
        assert isinstance(t, TRecord)  # TODO: Add support for other types.
        assert not t.fields  # TODO: Add support for non-empty records.
        t_ref = pyobj_creg.actor_to_ref(t)
        return htypes.builtin.call(
            function=t_ref,
            )
    return _data_to_res
