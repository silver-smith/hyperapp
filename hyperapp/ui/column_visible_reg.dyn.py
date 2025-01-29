from .code.mark import mark
from .code.data_service import DataServiceConfigCtl


@mark.service(ctl=DataServiceConfigCtl())
def column_visible_reg(config):
    return config
