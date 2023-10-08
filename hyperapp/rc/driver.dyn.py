import logging

from .services import (
    pyobj_creg,
    )

log = logging.getLogger(__name__)


def import_module(module_ref):
    log.info("Import module: %s", module_ref)
    module = pyobj_creg.invite(module_ref)
