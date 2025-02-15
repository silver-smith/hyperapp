from .code.mark import mark
from .code.multi_code_registry import MultiCodeRegistry


@mark.service
def adapter_creg(config):
    return MultiCodeRegistry('adapter_creg', config)
