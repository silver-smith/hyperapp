from . import htypes
from .code.mark import mark


@mark.model
def view_factory_list(piece, view_factory_reg):
    return list(view_factory_reg.values())


@mark.global_command
def open_view_factory_list():
    return htypes.view_factory_list.view()
