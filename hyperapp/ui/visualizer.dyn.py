import logging

from hyperapp.boot.htypes import TList

from . import htypes
from .services import (
    code_registry_ctr,
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


def _primitive_value_layout(t):
    if isinstance(t, TList):
        adapter = htypes.list_adapter.static_list_adapter()
        return htypes.list.view(mosaic.put(adapter))
    raise KeyError(t)


@mark.service
def visualizer_reg(config, t):
    try:
        model = config[t]
    except KeyError:
        raise
    ui_t = web.summon(model.ui_t)
    system_fn_ref = model.system_fn
    return (ui_t, system_fn_ref)


@mark.service
def ui_type_creg(config):
    return code_registry_ctr('ui_type_creg', config)


@mark.service
def visualizer(model_layout_reg, visualizer_reg, ui_type_creg, ctx, model_t):
    layout_k = htypes.ui.model_layout_k(
        model_t=pyobj_creg.actor_to_ref(model_t),
        )
    try:
        return model_layout_reg[layout_k]
    except KeyError:
        pass
    try:
        return _primitive_value_layout(model_t)
    except KeyError:
        pass
    try:
        ui_t, system_fn_ref = visualizer_reg(model_t)
    except KeyError:
        raise RuntimeError(f"No view for model is known: {model!r}")
    return ui_type_creg.animate(ui_t, system_fn_ref)
