from .services import (
    deduce_t,
    )
from .code.mark import mark


@mark.service
def default_model_factory(config, view_factory_reg, model_t):
    k = config[model_t]
    return view_factory_reg[k]


@mark.service
def default_ui_factory(config, view_factory_reg, ui_t):
    ui_t_t = deduce_t(ui_t)
    k = config[ui_t_t]
    return view_factory_reg[k]
