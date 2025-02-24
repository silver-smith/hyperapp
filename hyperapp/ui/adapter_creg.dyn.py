from .code.mark import mark
from .code.multi_code_registry import MultiCodeRegistry
from .code.list_config_ctl import DictListConfigCtl


@mark.service(ctl=DictListConfigCtl())
def adapter_creg(config):
    return MultiCodeRegistry('adapter_creg', config)
