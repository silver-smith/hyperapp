from types import SimpleNamespace

from .services import (
    pyobj_creg,
    )


def python_object(piece):
    attributes = {
        rec.name: pyobj_creg.invite(rec.resource)
        for rec in piece.attributes
        }
    return SimpleNamespace(**attributes)
