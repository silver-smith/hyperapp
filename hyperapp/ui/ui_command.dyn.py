import logging
from functools import partial

from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.mark import mark
from .code.command import UnboundCommand, BoundCommand, CommandKind
from .code.command_groups import default_command_groups
from .code.command_config_ctl import TypedCommandConfigCtl

log = logging.getLogger(__name__)


class UnboundUiCommand(UnboundCommand):

    def __init__(self, d, fn, ctx_params, groups):
        super().__init__(d, fn, ctx_params)
        self._groups = groups

    def bind(self, ctx):
        return BoundUiCommand(self._d, self._fn, self._ctx_params, ctx, self._groups)


class BoundUiCommand(BoundCommand):

    def __init__(self, d, fn, ctx_params, ctx, groups):
        super().__init__(d, fn, ctx_params, ctx)
        self._groups = groups

    @property
    def groups(self):
        return self._groups


@mark.actor.command_creg
def ui_command_from_piece(piece, system):
    kw = {
        name: system.resolve_service(name)
        for name in piece.service_params
        }
    fn = pyobj_creg.invite(piece.function)
    return UnboundUiCommand(
        d=pyobj_creg.invite(piece.d),
        fn=partial(fn, **kw),
        ctx_params=piece.ctx_params,
        groups=default_command_groups(piece.properties, CommandKind.VIEW),
        )


@mark.service2(ctl=TypedCommandConfigCtl())
def view_ui_command_reg(config, view_t):
    return config.get(view_t, [])


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
