from .services import (
    web,
    )
from .code.mark import mark
from .code.config_ctl import DataValueCtl, DictConfigCtl


@mark.service(ctl=DictConfigCtl(value_ctl=DataValueCtl()))
def model_reg(config):
    return config


@mark.service
def visualizer_reg(system_fn_creg, model_reg, t):
    try:
        model = model_reg[t]
    except KeyError:
        raise
    ui_t = web.summon(model.ui_t)
    system_fn = system_fn_creg.invite(model.system_fn)
    return (ui_t, system_fn)
