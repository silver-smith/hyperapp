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
from .code.model_command import model_commands


@mark.service
def visualizer():
    def fn(value):
        t = deduce_complex_value_type(mosaic, types, value)

        if t is tString:
            adapter_layout = htypes.str_adapter.static_str_adapter(value)
            return htypes.text.edit_layout(mosaic.put(adapter_layout))
        if isinstance(t, TList):
            adapter_layout = htypes.list_adapter.static_list_adapter(mosaic.put(value, t))
            return htypes.list.view(mosaic.put(adapter_layout))

        model_d_res = data_to_res(htypes.ui.model_d())
        t_res = pyobj_creg.reverse_resolve(t)
        try:
            model = association_reg[model_d_res, t_res]
        except KeyError:
            raise NotImplementedError(t)
        ui_t = web.summon(model.ui_t)
        impl = web.summon(model.impl)

        if isinstance(ui_t, htypes.ui.list_ui_t) and isinstance(impl, htypes.ui.fn_impl):
            adapter_layout = htypes.list_adapter.fn_list_adapter(
                model_piece=mosaic.put(value),
                element_t=ui_t.element_t,
                function=impl.function,
                want_feed=impl.want_feed,
                )
            view = htypes.list.view(mosaic.put(adapter_layout))

            if t is not htypes.sample_list.sample_list:
                return view

            command_list = model_commands(value)
            command = next(cmd for cmd in command_list if cmd.name == 'sample_list_state')
            details_adapter= htypes.str_adapter.static_str_adapter("Default details")
            details = htypes.text.view_layout(mosaic.put(details_adapter))
            return htypes.master_details.view(
                model=mosaic.put(value),
                master_view=mosaic.put(view),
                details_command=mosaic.put(command),
                details_view=mosaic.put(details),
                direction='LeftToRight',
                master_stretch=1,
                details_stretch=1,
                )

        if isinstance(ui_t, htypes.ui.tree_ui_t) and isinstance(impl, htypes.ui.fn_impl):
            adapter_layout = htypes.tree_adapter.fn_index_tree_adapter(
                model_piece=mosaic.put(value),
                element_t=ui_t.element_t,
                key_t=ui_t.key_t,
                function=impl.function,
                want_feed=impl.want_feed,
                )
            return htypes.tree.view(mosaic.put(adapter_layout))
        raise NotImplementedError(f"Not supported model: {ui_t} / {impl}")
    return fn
