from .services import (
    code_registry_ctr,
    mosaic,
    web,
    )
from .code.mark import mark


@mark.service
def command_creg(config):
    return code_registry_ctr('command_creg', config)
