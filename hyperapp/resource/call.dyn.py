from .services import (
    python_object_creg,
    )


def python_object(piece):
    fn = python_object_creg.invite(piece.function)
    return fn()
