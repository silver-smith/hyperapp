from .services import (
    code_registry_ctr2,
    mosaic,
    web,
    )
from .code.mark import mark


@mark.service2
def command_creg(config):
    return code_registry_ctr2('command', config)
