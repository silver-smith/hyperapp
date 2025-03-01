from .code.mark import mark
from .code.data_service import TypeKeyDataServiceConfigCtl


@mark.service(ctl=TypeKeyDataServiceConfigCtl())
def model_layout_reg(config):
    return config
