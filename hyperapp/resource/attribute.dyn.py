from .services import (
    python_object_creg,
    )


def python_object(piece):
    object = python_object_creg.invite(piece.object)
    return getattr(object, piece.attr_name)
