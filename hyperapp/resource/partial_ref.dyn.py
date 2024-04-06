from . import htypes
from .services import (
    fn_to_ref,
    mark,
    mosaic,
    )


@mark.service
def partial_ref():
    def _partial_ref(fn, **kw):
        partial = htypes.partial.partial(
            function=fn_to_ref(fn),
            params=tuple(
                htypes.partial.param(
                    name,
                    mosaic.put(htypes.raw.raw(
                        mosaic.put(value))))
                for name, value in kw.items()
                ),
            )
        return mosaic.put(partial)

    return _partial_ref
