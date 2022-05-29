import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


def register_impl(piece, python_object_creg, web, impl_registry):
    piece_t = python_object_creg.invite(piece.piece_t)
    ctr_fn = web.summon(piece.ctr_fn)
    spec = web.summon(piece.spec)
    log.info("Register implementation: %s -> %s, spec: %s", piece_t, ctr_fn, spec)
    impl_registry[piece_t] = (ctr_fn, spec)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.impl_registry = {}  # piece_t -> implementation record.
        services.meta_registry.register_actor(
            htypes.impl.impl_association, register_impl, services.python_object_creg, services.web, services.impl_registry)
