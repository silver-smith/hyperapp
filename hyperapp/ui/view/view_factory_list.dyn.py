from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.directory import k_to_name


@mark.model
def view_factory_list(piece, view_factory_reg):
    model_t = pyobj_creg.invite_opt(piece.model_t)
    return [
        factory.item for factory
        in view_factory_reg.values(model_t)
        ]


@mark.global_command
def open_view_factory_list():
    return htypes.view_factory_list.model(model_t=None)


@mark.editor.default
def pick_view_factory_context(ctx):
    try:
        model = ctx.model
    except KeyError:
        model_t = None
    else:
        model_t = deduce_t(model)
    return htypes.view_factory.factory(
        model_t=pyobj_creg.actor_to_ref_opt(model_t),
        k=None,
        )


@mark.selector.get
def view_factory_list_get(value):
    return htypes.view_factory_list.model(
        model_t=value.model_t,
        )


@mark.selector.pick
def view_factory_list_pick(piece, current_item):
    return htypes.view_factory.factory(
        model_t=None,
        k=current_item.k,
        )
