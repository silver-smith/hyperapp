from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.view_factory import ViewFactory, ViewMultiFactory


@mark.actor.cfg_value_creg
def resolve_view_factory_cfg_value(piece, key, system, service_name):
    system_fn_creg = system['system_fn_creg']
    if piece.model_t_list is not None:
        model_t_list = [
            pyobj_creg.invite(model_t) for model_t in piece.model_t_list
            ]
    else:
        model_t_list = None
    assert not (model_t_list is not None and piece.ui_t_t is not None)  # Not both.
    return ViewFactory(
        format=system['format'],
        visualizer_reg=system['visualizer_reg'],
        k=key,
        model_t_list=model_t_list,
        ui_t_t=pyobj_creg.invite_opt(piece.ui_t_t),
        view_t=pyobj_creg.invite(piece.view_t),
        is_wrapper=piece.is_wrapper,
        view_ctx_params=piece.view_ctx_params,
        system_fn=system_fn_creg.invite(piece.system_fn),
        )


@mark.actor.cfg_value_creg
def resolve_view_multi_factory_cfg_value(piece, key, system, service_name):
    system_fn_creg = system['system_fn_creg']
    if piece.model_t_list is not None:
        model_t_list = [
            pyobj_creg.invite(model_t) for model_t in piece.model_t_list
            ]
    else:
        model_t_list = None
    assert not (model_t_list is not None and piece.ui_t_t is not None)  # Not both.
    return ViewMultiFactory(
        format=system['format'],
        visualizer_reg=system['visualizer_reg'],
        k=key,
        model_t_list=model_t_list,
        ui_t_t=pyobj_creg.invite_opt(piece.ui_t_t),
        list_fn=system_fn_creg.invite(piece.list_fn),
        get_fn=system_fn_creg.invite(piece.get_fn),
        )
