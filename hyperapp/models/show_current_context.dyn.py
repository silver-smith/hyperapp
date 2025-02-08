from . import htypes
from .code.mark import mark


@mark.global_command
def show_current_context(ctx):
    item_list = []
    for name, value in ctx.as_dict().items():
        item = htypes.show_current_context.item(
            name=name,
            value=str(value),
            )
        item_list.append(item)
    return item_list
