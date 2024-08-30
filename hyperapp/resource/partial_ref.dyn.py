from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )


def partial_ref(fn, **kw):
    partial = htypes.builtin.partial(
        function=pyobj_creg.actor_to_ref(fn),
        params=tuple(
            htypes.builtin.partial_param(
                name,
                mosaic.put(htypes.builtin.raw(
                    mosaic.put(value))))
            for name, value in kw.items()
            ),
        )
    return mosaic.put(partial)
