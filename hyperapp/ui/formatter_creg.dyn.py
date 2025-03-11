from .services import (
    code_registry_ctr,
    )
from .code.mark import mark


@mark.service
def formatter_creg(config):
    return code_registry_ctr('formatter_creg', config)
