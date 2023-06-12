import logging

from ..common.association_registry import Association

log = logging.getLogger(__name__)


def register_pyobj_meta(python_object_creg, piece):
    t = python_object_creg.invite(piece.t)
    log.info("Register python association: %s -> %s", t, piece.function)
    return Association(
        bases=[t],
        key_to_value={(python_object_creg, t): piece.function},
        )
