import logging
from functools import cached_property

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.mark import mark
from .code.command import Command, CommandKind, FnCommandImpl
from .code.command_groups import default_command_groups
from .code.command_config_ctl import CommandConfigCtl

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
    pass


@mark.actor.ui_command_impl_creg(htypes.ui.ui_command_impl)
def ui_command_impl_from_piece(piece, ctx):
    fn = pyobj_creg.invite(piece.function)
    return UiCommandImpl(ctx, fn, piece.ctx_params)


@mark.service2(ctl=CommandConfigCtl())
def view_ui_command_reg(config, view_t):
    return config[view_t]


@mark.service2
def universal_ui_command_reg(config):
    return config


@mark.service2
def get_view_commands(view_ui_command_reg, universal_ui_command_reg, view):
    view_t = deduce_t(view.piece)
    return [
        *view_ui_command_reg(view_t),
        *universal_ui_command_reg,
        ]


@mark.service2
def ui_command_factory(ui_command_impl_creg, piece, ctx):
    command_d = pyobj_creg.invite(piece.d)
    impl = ui_command_impl_creg.invite(piece.impl, ctx)
    groups = default_command_groups(piece.properties, CommandKind.VIEW)
    return UiCommand(command_d, impl, groups)
