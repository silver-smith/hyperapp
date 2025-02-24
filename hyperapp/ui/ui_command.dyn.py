import logging
from functools import partial

from .services import (
    deduce_t,
    web,
    )
from .code.mark import mark
from .code.command import UnboundCommand, BoundCommand, CommandKind
from .code.command_enumerator import UnboundCommandEnumerator
from .code.command_groups import default_command_groups
from .code.list_config_ctl import DictListConfigCtl, FlatListConfigCtl
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
        d=web.summon(piece.d),
        ctx_fn=ctx_fn,
        properties=piece.properties,
        groups=default_command_groups(piece.properties, CommandKind.VIEW),
        )


@mark.actor.command_creg
def ui_command_enumerator_from_piece(piece, system_fn_creg):
    ctx_fn = system_fn_creg.invite(piece.system_fn)
    return UnboundCommandEnumerator(
        ctx_fn=ctx_fn,
        )


@mark.service(ctl=DictListConfigCtl())
def view_ui_command_reg(config, view_t):
    return config.get(view_t, [])


# UI commands returning model.
@mark.service(ctl=DictListConfigCtl())
def view_ui_model_command_reg(config, view_t):
    return config.get(view_t, [])


@mark.service(ctl=FlatListConfigCtl())
def universal_ui_command_reg(config):
    return config


@mark.service(ctl=DictListConfigCtl())
def ui_command_enumerator_reg(config, view_t):
    return config.get(view_t, [])


@mark.service
def get_view_commands(
        view_reg,
        visualizer,
        view_ui_command_reg,
        view_ui_model_command_reg,
        universal_ui_command_reg,
        ui_command_enumerator_reg,
        ctx,
        lcs,
        view,
        ):
    view_t = deduce_t(view.piece)
    ui_model_command_list = [
        wrap_model_command_to_ui_command(view_reg, visualizer, lcs, cmd)
        for cmd in view_ui_model_command_reg(view_t)
        ]
    command_list = [
        *view_ui_command_reg(view_t),
        *ui_model_command_list,
        *universal_ui_command_reg,
        ]
    for enumerator in ui_command_enumerator_reg(view_t):
        command_list += enumerator.enum_commands(ctx)
    return command_list
