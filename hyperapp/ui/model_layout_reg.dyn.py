from .code.mark import mark
from .code.data_service import DataServiceConfigCtl


@mark.service(ctl=DataServiceConfigCtl())
def model_layout_reg(config):
    return config
