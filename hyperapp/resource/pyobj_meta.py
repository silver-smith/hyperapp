import logging

from ..common.association_registry import Association

log = logging.getLogger(__name__)


def register_pyobj_meta(python_object_creg, piece):
    t = python_object_creg.invite(piece.t)
    function = python_object_creg.invite(piece.function)
    log.info("Register python object: %s -> %s", t, function)
    python_object_creg.register_actor(t, function)
    # Register manually because python_object_creg does not support association_reg lookup.
    # But also return base so that it would be bundled with registered type.
    return Association(
        bases=[t],
        key_to_value={},
        )
