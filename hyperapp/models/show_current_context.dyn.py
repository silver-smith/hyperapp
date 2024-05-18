from . import htypes


def current_context_list(piece, ctx):
    item_list = []
    for name, value in ctx.as_dict().items():
        item = htypes.show_current_context.item(
            name=name,
            value=str(value),
            )
        item_list.append(item)
    return item_list


def show_current_context(piece):
    return htypes.show_current_context.view()
