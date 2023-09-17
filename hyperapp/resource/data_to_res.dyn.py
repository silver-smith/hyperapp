from hyperapp.common.htypes.call import call_t
from hyperapp.common.htypes import TRecord
from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from .services import (
    mark,
    mosaic,
    pyobj_creg,
    )


@mark.service
def data_to_res():
    def _data_to_res(piece):
        t = deduce_value_type(piece)
        assert isinstance(t, TRecord)  # TODO: Add support for other types.
        assert not t.fields  # TODO: Add support for non-empty records.
        t_res = pyobj_creg.reverse_resolve(t)
        return call_t(mosaic.put(t_res))
    return _data_to_res
