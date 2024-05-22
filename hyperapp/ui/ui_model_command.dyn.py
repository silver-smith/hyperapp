import logging

from . import htypes
from .services import (
    enum_model_commands,
    global_commands,
    mark,
    model_command_impl_creg,
    model_command_factory,
    pyobj_creg,
    ui_command_impl_creg,
    model_view_creg,
    mosaic,
    visualizer,
    )
from .code.command import CommandImpl

log = logging.getLogger(__name__)


class UiModelCommandImpl(CommandImpl):

    def __init__(self, ctx, model_command):
        super().__init__()
        self._ctx = ctx
        self._navigator_rec = ctx.navigator
        self._lcs = ctx.lcs
        self._model_command = model_command

    @property
    def name(self):
        return self._model_command.name

    @property
    def enabled(self):
        return self._model_command.enabled

    @property
    def disabled_reason(self):
        return self._model_command.disabled_reason

    async def _run(self):
        navigator_w = self._navigator_rec.widget_wr()
        if navigator_w is None:
            raise RuntimeError("Navigator widget is gone")
        piece = await self._model_command.run()
        if piece is None:
            return None
        if type(piece) is list:
            piece = tuple(piece)
        view_piece = visualizer(self._lcs, piece)
        view = model_view_creg.animate(view_piece, piece, self._ctx)
        log.info("Run model command %r view: %s", self.name, view)
        self._navigator_rec.view.open(self._ctx, piece, view, navigator_w)


@ui_command_impl_creg.actor(htypes.ui.ui_model_command_impl)
def ui_model_command_impl_from_piece(piece, ctx):
    model_command = model_command_impl_creg.invite(piece.model_command_impl, ctx)
    return UiModelCommandImpl(ctx, model_command)


@mark.service
def ui_model_command_factory():
    def _ui_model_command_factory(piece, ctx):
        model_commands = [
            *global_commands(),
            *model_command_factory(piece),
            *enum_model_commands(piece, ctx),
            ]
        return [
            htypes.ui.ui_model_command(
                d=cmd.d,
                name=cmd.name,
                model_command=mosaic.put(cmd),
                )
            for cmd in model_commands
            ]
    return _ui_model_command_factory
