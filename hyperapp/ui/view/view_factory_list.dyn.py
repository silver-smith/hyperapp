from . import htypes
from .code.mark import mark


@mark.model
def view_factory_list(piece, view_factory_reg):
    return [factory.item for factory in view_factory_reg.values()]


@mark.global_command
def open_view_factory_list():
    return htypes.view_factory_list.view()


@mark.selector.get
def view_factory_list_get(value):
    return htypes.view_factory_list.view()


@mark.selector.pick
def view_factory_list_pick(piece, current_item):
    return htypes.view_factory.factory(
        k=current_item.k,
        )
