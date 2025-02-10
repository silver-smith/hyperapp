from .code.mark import mark
from .code.context_code_registry import ContextCodeRegistry


@mark.service
def view_reg(config):
    return ContextCodeRegistry('view_reg', config)
