from functools import partial

from .services import (
    pyobj_creg,
    )


def python_object(piece):
    fn = pyobj_creg.invite(piece.function)
    kw = {
        param.name: pyobj_creg.invite(param.value)
        for param in piece.params
        }
    return partial(fn, **kw)
