from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    mark,
    mosaic,
    pyobj_creg,
    )


@mark.service
def data_to_res():
    def _data_to_res(piece, t=None):
        if t is None:
            t = deduce_t(piece)
        assert isinstance(t, TRecord)  # TODO: Add support for other types.
        t_ref = pyobj_creg.actor_to_ref(t)
        if t.fields:
            params = tuple(
                htypes.partial.param(
                    name=name,
                    value=mosaic.put(
                        htypes.raw.raw(
                            mosaic.put(
                                getattr(piece, name)))),
                    )
                for name in t.fields
                )
            partial = htypes.partial.partial(
                function=t_ref,
                params=params,
                )
            fn_ref = mosaic.put(partial)
        else:
            fn_ref = t_ref
        return htypes.builtin.call(
            function=fn_ref,
            )
    return _data_to_res
