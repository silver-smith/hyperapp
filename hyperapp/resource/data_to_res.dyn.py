from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark


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


@mark.service2
def data_to_res(piece, t=None):
    return _data_to_res(piece, t)


@mark.service2
def data_to_ref(piece, t=None):
    return mosaic.put(_data_to_res(piece, t))
