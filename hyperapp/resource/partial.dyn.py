from functools import partial

from .services import (
    python_object_creg,
    )


def python_object(piece):
    fn = python_object_creg.invite(piece.function)
    kw = {
        param.name: python_object_creg.invite(param.value)
        for param in piece.params
        }
    return partial(fn, **kw)
