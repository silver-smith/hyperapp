from .services import (
    code_registry_ctr,
    )
from .code.mark import mark


@mark.service
def diff_creg(config):
    return code_registry_ctr('diff_creg', config)
