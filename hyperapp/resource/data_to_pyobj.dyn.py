from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    )


def data_to_pyobj(piece, t=None):
    if t is None:
        t = deduce_t(piece)
    assert isinstance(t, TRecord)  # TODO: Add support for other types.
    t_ref = pyobj_creg.actor_to_ref(t)
    if t.fields:
        params = tuple(
            htypes.builtin.partial_param(
                name=name,
                value=mosaic.put(
                    htypes.builtin.raw(
                        mosaic.put(
                            getattr(piece, name)))),
                )
            for name in t.fields
            )
        partial = htypes.builtin.partial(
            function=t_ref,
            params=params,
            )
        fn_ref = mosaic.put(partial)
    else:
        fn_ref = t_ref
    return htypes.builtin.call(
        function=fn_ref,
        )


def data_to_pyobj_ref(data_to_pyobj, piece, t=None):
    return mosaic.put(data_to_pyobj(piece, t))
