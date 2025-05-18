from . import htypes
from .services import (
    code_registry_ctr,
    mosaic,
    )
from .code.mark import mark


@mark.service
def accessor_creg(config):
    return code_registry_ctr('accessor_creg', config)
