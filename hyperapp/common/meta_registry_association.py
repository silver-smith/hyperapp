from functools import partial

from .htypes.meta_association import meta_association


def register_meta(meta_registry, python_object_creg, piece):
    t = python_object_creg.invite(piece.t)
    fn = python_object_creg.invite(piece.fn)
    meta_registry.register_actor(t, fn)


def register_meta_association(meta_registry, python_object_creg):
    meta_registry.register_actor(
        meta_association,
        partial(register_meta, meta_registry, python_object_creg),
        )
