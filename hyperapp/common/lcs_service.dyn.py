import logging

from hyperapp.common.module import Module

from . import htypes
from .lcs import LCSheet

log = logging.getLogger(__name__)


def register_association(piece, lcs):
    lcs._add_association(piece, persist=False)


def register_resource_association(piece, web, lcs):
    dir = [
        web.summon(ref)
        for ref in piece.dir
        ]
    value = web.summon(piece.value)
    if isinstance(piece, htypes.lcs.lcs_resource_association):
        record = lcs._set(dir, value, persist=False)
    else:
        assert isinstance(piece, htypes.lcs.lcs_set_resource_association)
        record = lcs._add(dir, value, persist=False)
    log.info("LCS: resource association: %s -> %s", set(dir), record)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        lcs = LCSheet(services.mosaic, services.web)
        services.lcs = lcs
        services.aux_bundler_hooks.append(lcs.aux_bundler_hook)

        services.meta_registry.register_actor(
            htypes.lcs.lcs_resource_association, register_resource_association, services.web, services.lcs)
        services.meta_registry.register_actor(
            htypes.lcs.lcs_set_resource_association, register_resource_association, services.web, services.lcs)
