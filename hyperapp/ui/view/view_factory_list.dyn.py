from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.directory import k_to_name


@mark.model
def view_factory_list(piece, view_factory_reg):
    model = web.summon_opt(piece.model)
    return view_factory_reg.items(model)


@mark.global_command
def open_view_factory_list():
    return htypes.view_factory_list.model(model=None)


@mark.editor.default
def pick_view_factory_context(ctx):
    try:
        model = ctx.model
    except KeyError:
        model = None
    return htypes.view_factory.factory(
        model=mosaic.put_opt(model),
        k=None,
        )


@mark.selector.get
def view_factory_list_get(value):
    return htypes.view_factory_list.model(
        model=value.model,
        )


@mark.selector.pick
def view_factory_list_pick(piece, current_item):
    return htypes.view_factory.factory(
        model=None,
        k=current_item.k,
        )
