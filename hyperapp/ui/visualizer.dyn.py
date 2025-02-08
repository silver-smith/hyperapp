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


@mark.service
def model_layout_creg(config):
    return code_registry_ctr('model_layout_creg', config)


@mark.actor.model_layout_creg
def string_layout(piece, lcs, ctx):
    adapter = htypes.str_adapter.static_str_adapter()
    return htypes.text.edit_view(mosaic.put(adapter))


@mark.actor.model_layout_creg
def int_layout(piece, lcs, ctx):
    adapter = htypes.int_adapter.int_adapter()
    return htypes.text.edit_view(mosaic.put(adapter))


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
def get_custom_layout(lcs, t):
    t_res = pyobj_creg.actor_to_piece(t)
    d = {
        htypes.ui.model_view_layout_d(),
        t_res,
        }
    return lcs.get(d)


@mark.service
def set_custom_layout(lcs, t, layout):
    log.info("Save layout for %s: %s", t, layout)
    t_res = pyobj_creg.actor_to_piece(t)
    d = {
        htypes.ui.model_view_layout_d(),
        t_res,
        }
    lcs.set(d, layout)


@mark.service
def visualizer(model_layout_creg, visualizer_reg, ui_type_creg, get_custom_layout, lcs, ctx, model):
    try:
        return model_layout_creg.animate(model, lcs, ctx)
    except KeyError:
        pass
    model_t = deduce_t(model)
    try:
        return _primitive_value_layout(model_t)
    except KeyError:
        pass
    view = get_custom_layout(lcs, model_t)
    if view is not None:
        log.info("Using configured layout for %s: %s", model_t, view)
        return view
    try:
        ui_t, system_fn_ref = visualizer_reg(model_t)
    except KeyError:
        raise RuntimeError(f"No view for model is known: {model!r}")
    return ui_type_creg.animate(ui_t, system_fn_ref)
