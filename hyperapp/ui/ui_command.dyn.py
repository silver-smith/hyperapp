import logging
from functools import partial

from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.mark import mark
from .code.command import UnboundCommand, BoundCommand, CommandKind
from .code.command_groups import default_command_groups
from .code.command_config_ctl import TypedCommandConfigCtl, UntypedCommandConfigCtl
from .code.ui_model_command import wrap_model_command_to_ui_command

log = logging.getLogger(__name__)


class UnboundUiCommand(UnboundCommand):

    def __init__(self, d, ctx_fn, properties, groups):
        super().__init__(d, ctx_fn)
        self._properties = properties
        self._groups = groups

    @property
    def properties(self):
        return self._properties

    def bind(self, ctx):
        return BoundUiCommand(self._d, self._ctx_fn, ctx, self._properties, self._groups)


class BoundUiCommand(BoundCommand):

    def __init__(self, d, ctx_fn, ctx, properties, groups):
        super().__init__(d, ctx_fn, ctx)
        self._properties = properties
        self._groups = groups

    @property
    def properties(self):
        return self._properties

    @property
    def groups(self):
        return self._groups


@mark.actor.command_creg
def ui_command_from_piece(piece, system_fn_creg):
    ctx_fn = system_fn_creg.invite(piece.system_fn)
    return UnboundUiCommand(
        d=pyobj_creg.invite(piece.d),
        ctx_fn=ctx_fn,
        properties=piece.properties,
        groups=default_command_groups(piece.properties, CommandKind.VIEW),
        )


@mark.service2(ctl=TypedCommandConfigCtl())
def view_ui_command_reg(config, view_t):
    return config.get(view_t, [])


# UI commands returning model.
@mark.service2(ctl=TypedCommandConfigCtl())
def view_ui_model_command_reg(config, view_t):
    return config.get(view_t, [])


@mark.service2(ctl=UntypedCommandConfigCtl())
def universal_ui_command_reg(config):
    return config


@mark.service2
def get_view_commands(model_view_creg, visualizer, view_ui_command_reg, view_ui_model_command_reg, universal_ui_command_reg, lcs, view):
    view_t = deduce_t(view.piece)
    ui_model_command_list = [
        wrap_model_command_to_ui_command(model_view_creg, visualizer, lcs, cmd)
        for cmd in view_ui_model_command_reg(view_t)
        ]
    return [
        *view_ui_command_reg(view_t),
        *ui_model_command_list,
        *universal_ui_command_reg,
        ]
