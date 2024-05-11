import logging

from hyperapp.common.htypes import tString, TList
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    mark,
    mosaic,
    pyobj_creg,
    types,
    web,
    )

log = logging.getLogger(__name__)


def _primitive_value_layout(t, value):
    if t is tString:
        adapter = htypes.str_adapter.static_str_adapter()
        return htypes.text.edit_view(mosaic.put(adapter))
    if isinstance(t, TList):
        adapter = htypes.list_adapter.static_list_adapter()
        return htypes.list.view(mosaic.put(adapter))
    return None


def _configured_layout(lcs, t, value):
    t_res = pyobj_creg.reverse_resolve(t)
    d = {
        htypes.ui.model_view_layout_d(),
        t_res,
        }
    return lcs.get(d)


def _default_layout(t, value):
    model_d_res = data_to_res(htypes.ui.model_d())
    t_res = pyobj_creg.reverse_resolve(t)
    try:
        model = association_reg[model_d_res, t_res]
    except KeyError:
        raise RuntimeError(f"No implementation is registered for model: {t}")
    ui_t = web.summon(model.ui_t)
    impl = web.summon(model.impl)

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

    raise NotImplementedError(f"Not supported model: {ui_t} / {impl}")


@mark.service
def visualizer():
    def fn(lcs, value):
        t = deduce_complex_value_type(mosaic, types, value)

        view = _primitive_value_layout(t, value)
        if view is not None:
            return view

        view = _configured_layout(lcs, t, value)
        if view is not None:
            log.info("Using configured layout for %s: %s", t, view)
            return view

        return _default_layout(t, value)

    return fn
