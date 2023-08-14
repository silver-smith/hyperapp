import logging

from ..common.association_registry import Association

log = logging.getLogger(__name__)


def register_pyobj_meta(web, piece):
    assert 0  # Unused?
    t_res = web.summon(piece.t)
    log.info("Register python association: %s -> %s", t_res, piece.function)
    return Association(
        bases=[t_res],
        key_to_value={(python_object_creg, t_res): piece.function},
        )
