import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


def register_impl(piece, python_object_creg, web, impl_registry):
    piece_t = python_object_creg.invite(piece.piece_t)
    impl = web.summon(piece.implementation)
    log.info("Register implementation: %s -> %s", piece_t, impl)
    impl_registry[piece_t] = impl


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.impl_registry = {}  # piece_t -> implementation record.
        services.meta_registry.register_actor(
            htypes.impl.impl_association, register_impl, services.python_object_creg, services.web, services.impl_registry)
