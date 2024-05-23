import logging
from functools import cached_property

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    deduce_t,
    mark,
    mosaic,
    pyobj_creg,
    ui_command_impl_creg,
    )
from .code.command import Command, FnCommandImpl
from .code.command_groups import default_command_groups

log = logging.getLogger(__name__)



class UiCommand(Command):

    def __init__(self, d, impl, groups):
        super().__init__(d, impl)
        self._groups = groups

    def __repr__(self):
        return f"<UiCommand: {self.name}: {self._impl}>"

    @property
    def groups(self):
        return self._groups


class UiCommandImpl(FnCommandImpl):

    def __init__(self, ctx, fn, params, properties):
        super().__init__(ctx, fn, params)
        self._properties = properties

    @property
    def properties(self):
        return self._properties


@ui_command_impl_creg.actor(htypes.ui.ui_command_impl)
def ui_command_impl_from_piece(piece, ctx):
    command_properties_d_res = data_to_res(htypes.ui.command_properties_d())
    fn = pyobj_creg.invite(piece.function)
    properties = association_reg[command_properties_d_res, piece]
    return UiCommandImpl(ctx, fn, piece.params, properties)


@mark.service
def list_view_commands():
    def _list_view_commands(view):
        piece_t = deduce_t(view.piece)
        piece_t_res = pyobj_creg.reverse_resolve(piece_t)
        d_res = data_to_res(htypes.ui.ui_command_d())
        universal_d_res = data_to_res(htypes.ui.universal_ui_command_d())
        command_list = [
            *association_reg.get_all((d_res, piece_t_res)),
            *association_reg.get_all(universal_d_res),
            ]
        return command_list
    return _list_view_commands


@mark.service
def ui_command_factory():
    def _ui_command_factory(piece, ctx):
        command_d = pyobj_creg.invite(piece.d)
        impl = ui_command_impl_creg.invite(piece.impl, ctx)
        groups = default_command_groups(impl.properties)
        return UiCommand(command_d, impl, groups)

    return _ui_command_factory
