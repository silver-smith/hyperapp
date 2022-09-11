from . import htypes
from .services import (
    python_object_creg,
    meta_registry,
    )


def register_meta(piece):
    t = python_object_creg.invite(piece.t)
    fn = python_object_creg.invite(piece.fn)
    meta_registry.register_actor(t, fn)


def init():
    meta_registry.register_actor(
        htypes.meta_registry.meta_association,
        register_meta,
        )
