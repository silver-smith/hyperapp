import logging

from hyperapp.common.htypes import tInt, tString, TList

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


def _primitive_value_layout(t):
    if t is tString:
        adapter = htypes.str_adapter.static_str_adapter()
        return htypes.text.edit_view(mosaic.put(adapter))
    if t is tInt:
        adapter = htypes.int_adapter.int_adapter()
        return htypes.text.edit_view(mosaic.put(adapter))
    if isinstance(t, TList):
        adapter = htypes.list_adapter.static_list_adapter()
        return htypes.list.view(mosaic.put(adapter))
    return None


def _model_layout(visualizer_reg, t):
    ui_t, system_fn_ref = visualizer_reg(t)

    if isinstance(ui_t, htypes.model.list_ui_t):
        adapter = htypes.list_adapter.fn_list_adapter(
            element_t=ui_t.element_t,
            system_fn=system_fn_ref,
            )
        return htypes.list.view(mosaic.put(adapter))

    if isinstance(ui_t, htypes.model.tree_ui_t):
        adapter = htypes.tree_adapter.fn_index_tree_adapter(
            element_t=ui_t.element_t,
            # key_t=ui_t.key_t,
            system_fn=system_fn_ref,
            )
        return htypes.tree.view(mosaic.put(adapter))

    if isinstance(ui_t, htypes.model.record_ui_t):
        adapter = htypes.record_adapter.fn_record_adapter(
            record_t=ui_t.record_t,
            system_fn=system_fn_ref,
            )
        return htypes.form.view(mosaic.put(adapter))

    raise NotImplementedError(f"Not supported model: {ui_t} / {impl}")


@mark.service2
def visualizer_reg(config, t):
    try:
        model = config[t]
    except KeyError:
        raise KeyError(f"No implementation is registered for model: {t}")
    ui_t = web.summon(model.ui_t)
    system_fn_ref = model.system_fn
    return (ui_t, system_fn_ref)


@mark.service2
def get_custom_layout(lcs, t):
    t_res = pyobj_creg.actor_to_piece(t)
    d = {
        htypes.ui.model_view_layout_d(),
        t_res,
        }
    return lcs.get(d)


@mark.service2
def set_custom_layout(lcs, t, layout):
    log.info("Save layout for %s: %s", t, layout)
    t_res = pyobj_creg.actor_to_piece(t)
    d = {
        htypes.ui.model_view_layout_d(),
        t_res,
        }
    lcs.set(d, layout)


@mark.service2
def visualizer(visualizer_reg, get_custom_layout, lcs, value):
    t = deduce_t(value)

    view = _primitive_value_layout(t)
    if view is not None:
        return view

    view = get_custom_layout(lcs, t)
    if view is not None:
        log.info("Using configured layout for %s: %s", t, view)
        return view

    return _model_layout(visualizer_reg, t)
