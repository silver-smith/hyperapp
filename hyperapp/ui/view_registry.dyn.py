from .services import (
    code_registry_ctr,
    )
from .code.mark import mark


@mark.service2
def view_creg(config):
    return code_registry_ctr('view_creg', config)


@mark.service2
def model_view_creg(config):
    return code_registry_ctr('model_view_creg', config)
