import logging

log = logging.getLogger(__name__)


def register_pyobj_meta(python_object_creg, piece):
    t = python_object_creg.invite(piece.t)
    function = python_object_creg.invite(piece.function)
    log.info("Register python object: %s -> %s", t, function)
    python_object_creg.register_actor(t, function)
