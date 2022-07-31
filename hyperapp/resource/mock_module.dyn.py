from types import SimpleNamespace

from .services import (
    python_object_creg,
    )


def python_object(piece):
    attributes = {
        rec.name: python_object_creg.invite(rec.resource)
        for rec in piece.attributes
        }
    return SimpleNamespace(**attributes)
