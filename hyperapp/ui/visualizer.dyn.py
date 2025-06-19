import logging

from hyperapp.boot.htypes import TList
from hyperapp.boot.config_key_error import ConfigItemMissingError

from . import htypes
from .services import (
    code_registry_ctr,
    deduce_t,
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


def _static_list_ui_t(list_t):
    return htypes.model.static_list_ui_t(
        item_t=pyobj_creg.actor_to_ref(list_t.element_t),
        )


@mark.service
async def visualizer(
        model_layout_reg, visualizer_reg, default_model_factory, default_ui_factory,
        ctx, model_t, accessor=None, properties=None, **kw):
    layout_k = htypes.ui.model_layout_k(
        model_t=pyobj_creg.actor_to_ref(model_t),
        )
    try:
        return model_layout_reg[layout_k]
    except ConfigItemMissingError:
        pass
    all_properties = {**(properties or {}), **kw}
    try:
        factory = default_model_factory(model_t, all_properties)
    except ConfigItemMissingError:
        pass
    else:
        return await factory.call(ctx, model_t=model_t, accessor=accessor)
    try:
        ui_t, system_fn = visualizer_reg(model_t)
    except ConfigItemMissingError:
        if isinstance(model_t, TList):
            ui_t = _static_list_ui_t(model_t)
            system_fn = None
        else:
            raise RuntimeError(f"No view is known for model: {model_t!r}")
    factory = default_ui_factory(ui_t)
    return await factory.call_ui_t(ctx, ui_t, system_fn, accessor=accessor)


@mark.actor.resource_name_creg
def model_layout_k_resource_name(piece, gen):
    model_t = pyobj_creg.invite(piece.model_t)
    return f'{model_t.full_name}-model_layout_k'


@mark.actor.formatter_creg
def format_model_layout_k(piece):
    model_t = pyobj_creg.invite(piece.model_t)
    return f'model_layout_k({model_t.full_name})'
