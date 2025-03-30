from hyperapp.boot.htypes.deduce_value_type import DeduceTypeError

from . import htypes
from .code.mark import mark


@mark.model
def current_context_model(piece):
    return piece.items


@mark.global_command
def show_current_context(ctx, format):
    item_list = []
    for name, value in ctx.as_dict().items():
        try:
            title = format(value)
        except DeduceTypeError:
            title = ''
        item = htypes.show_current_context.item(
            name=name,
            value=str(value),
            title=title,
            )
        item_list.append(item)
    return htypes.show_current_context.model(
        items=tuple(item_list),
        )


@mark.actor.formatter_creg
def format_model(piece):
    return "Context"
