import logging
from functools import partial

from .htypes.meta_association import meta_association_t
from .association_registry import Association

log = logging.getLogger(__name__)


def register_meta(meta_registry, python_object_creg, piece):
    assert 0  # Unused?
    t = python_object_creg.invite(piece.t)
    log.info("Register meta association: %s -> %s", t, piece.fn)
    return Association(
        bases=[t],
        key_to_value={(meta_registry, t): piece.fn},
        )


def register_meta_association(meta_registry, python_object_creg):
    meta_registry.register_actor(
        meta_association_t,
        partial(register_meta, meta_registry, python_object_creg),
        )
