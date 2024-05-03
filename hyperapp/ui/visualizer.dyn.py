from hyperapp.common.htypes import tString, TList
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    mark,
    model_command_factory,
    mosaic,
    pyobj_creg,
    types,
    web,
    )


def _primitive_value_layout(t, value):
    if t is tString:
        adapter = htypes.str_adapter.static_str_adapter()
        return htypes.text.edit_view(mosaic.put(adapter))
    if isinstance(t, TList):
        adapter = htypes.list_adapter.static_list_adapter()
        return htypes.list.view(mosaic.put(adapter))
    return None


def _configured_layout(lcs, t, value):
    return None


def _default_layout(t, value):
    model_d_res = data_to_res(htypes.ui.model_d())
    t_res = pyobj_creg.reverse_resolve(t)
    try:
        model = association_reg[model_d_res, t_res]
    except KeyError:
        raise NotImplementedError(t)
    ui_t = web.summon(model.ui_t)
    impl = web.summon(model.impl)

    if isinstance(ui_t, htypes.ui.list_ui_t) and isinstance(impl, htypes.ui.fn_impl):
        adapter = htypes.list_adapter.fn_list_adapter(
            element_t=ui_t.element_t,
            function=impl.function,
            params=impl.params,
            )
        view = htypes.list.view(mosaic.put(adapter))

        if t is not htypes.sample_list.sample_list:
            return view

        command_list = model_command_factory(value)
        command = next(cmd for cmd in command_list if cmd.name == 'details')
        details_adapter = htypes.str_adapter.static_str_adapter()
        details = htypes.text.readonly_view(mosaic.put(details_adapter))
        return htypes.master_details.view(
            master_view=mosaic.put(view),
            details_command=mosaic.put(command),
            direction='LeftToRight',
            master_stretch=1,
            details_stretch=1,
            )

    if isinstance(ui_t, htypes.ui.tree_ui_t) and isinstance(impl, htypes.ui.fn_impl):
        adapter = htypes.tree_adapter.fn_index_tree_adapter(
            element_t=ui_t.element_t,
            key_t=ui_t.key_t,
            function=impl.function,
            params=impl.params,
            )
        return htypes.tree.view(mosaic.put(adapter))

    return None


@mark.service
def visualizer():
    def fn(lcs, value):
        t = deduce_complex_value_type(mosaic, types, value)

        view = _primitive_value_layout(t, value)
        if view is not None:
            return view

        view = _configured_layout(lcs, t, value)
        if view is not None:
            return view

        view = _default_layout(t, value)
        if view is not None:
            return view

        raise NotImplementedError(f"Not supported model: {ui_t} / {impl}")
    return fn
