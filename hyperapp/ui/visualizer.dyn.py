import logging

from hyperapp.common.htypes import tInt, tString, TList

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    deduce_t,
    mark,
    mosaic,
    pyobj_creg,
    web,
    )

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


def _configured_layout(lcs, t):
    t_res = pyobj_creg.reverse_resolve(t)
    d = {
        htypes.ui.model_view_layout_d(),
        t_res,
        }
    return lcs.get(d)


def _visualizer_info(t):
    model_d_res = data_to_res(htypes.ui.model_d())
    t_res = pyobj_creg.reverse_resolve(t)
    try:
        model = association_reg[model_d_res, t_res]
    except KeyError:
        raise RuntimeError(f"No implementation is registered for model: {t}")
    ui_t = web.summon(model.ui_t)
    impl = web.summon(model.impl)
    return (ui_t, impl)


def _default_layout(t):
    ui_t, impl = _visualizer_info(t)

    if isinstance(ui_t, htypes.ui.list_ui_t) and isinstance(impl, htypes.ui.fn_impl):
        adapter = htypes.list_adapter.fn_list_adapter(
            element_t=ui_t.element_t,
            function=impl.function,
            params=impl.params,
            )
        return htypes.list.view(mosaic.put(adapter))

    if isinstance(ui_t, htypes.ui.tree_ui_t) and isinstance(impl, htypes.ui.fn_impl):
        adapter = htypes.tree_adapter.fn_index_tree_adapter(
            element_t=ui_t.element_t,
            key_t=ui_t.key_t,
            function=impl.function,
            params=impl.params,
            )
        return htypes.tree.view(mosaic.put(adapter))

    if isinstance(ui_t, htypes.ui.record_ui_t) and isinstance(impl, htypes.ui.fn_impl):
        adapter = htypes.record_adapter.fn_record_adapter(
            record_t=ui_t.record_t,
            function=impl.function,
            params=impl.params,
            )
        return htypes.form.view(mosaic.put(adapter))

    raise NotImplementedError(f"Not supported model: {ui_t} / {impl}")


@mark.service
def pick_visualizer_info():
    return _visualizer_info


@mark.service
def visualizer():
    def fn(lcs, value):
        t = deduce_t(value)

        view = _primitive_value_layout(t)
        if view is not None:
            return view

        view = _configured_layout(lcs, t)
        if view is not None:
            log.info("Using configured layout for %s: %s", t, view)
            return view

        return _default_layout(t)

    return fn
