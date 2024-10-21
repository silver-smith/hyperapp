from .services import (
    code_registry_ctr2,
    )
from .code.mark import mark


@mark.service2
def view_creg(config):
    return code_registry_ctr2('view_creg', config)


@mark.service2
def model_view_creg(config):
    return code_registry_ctr2('model_view_creg', config)
