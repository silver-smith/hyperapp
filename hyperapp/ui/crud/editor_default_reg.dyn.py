from .code.mark import mark
from .code.config_ctl import DataValueCtl, DictConfigCtl


@mark.service(ctl=DictConfigCtl(value_ctl=DataValueCtl()))
def editor_default_reg(config):
    return config
