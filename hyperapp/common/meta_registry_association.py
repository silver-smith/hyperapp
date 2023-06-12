from functools import partial

from .htypes.meta_association import meta_association
from .association_registry import Association


def register_meta(meta_registry, python_object_creg, piece):
    t = python_object_creg.invite(piece.t)
    fn = python_object_creg.invite(piece.fn)
    meta_registry.register_actor(t, fn)
    # Register manually because meta_registry does not support association_reg lookup.
    # But also return base so that it would be bundled with registered type.
    return Association(
        bases=[t],
        key_to_value={},
        )


def register_meta_association(meta_registry, python_object_creg):
    meta_registry.register_actor(
        meta_association,
        partial(register_meta, meta_registry, python_object_creg),
        )
