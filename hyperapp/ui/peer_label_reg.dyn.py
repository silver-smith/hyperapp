from .code.mark import mark
from .code.data_service import DataServiceConfigCtl


@mark.service(ctl=DataServiceConfigCtl())
def peer_label_reg(config):
    return config
