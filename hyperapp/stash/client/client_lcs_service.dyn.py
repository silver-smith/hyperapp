import logging
from pathlib import Path

from hyperapp.common.module import Module

from . import htypes
from .lcs import LCSheet

log = logging.getLogger(__name__)


lcs_path = Path('~/.local/share/hyperapp/client/lcs.cdr').expanduser()


def register_association(piece, lcs):
    lcs.register_association(piece)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        bundle = services.file_bundle(lcs_path, encoding='cdr')
        lcs = LCSheet(services.mosaic, services.web, bundle)
        services.lcs = lcs
        services.aux_bundler_hooks.append(lcs.aux_bundler_hook)
        services.aux_unbundler_hooks.append(lcs.aux_unbundler_hook)

        services.meta_registry.register_actor(htypes.lcs.lcs_association, register_association, services.lcs)
        services.meta_registry.register_actor(htypes.lcs.lcs_set_association, register_association, services.lcs)
