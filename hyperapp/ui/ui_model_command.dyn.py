import logging

from .services import (
    enum_model_commands,
    global_commands,
    mark,
    model_command_creg,
    model_command_factory,
    view_creg,
    visualizer,
    )
from .code.ui_command import CommandBase

log = logging.getLogger(__name__)


class UiModelWrapperCommand(CommandBase):

    @classmethod
    def from_model_command(cls, model_command, ctx):
        return cls(model_command.name, model_command.d, ctx, model_command)

    def __init__(self, name, d, ctx, model_command):
        super().__init__(name, d)
        self._ctx = ctx
        self._navigator = ctx.navigator
        self._model_command = model_command

    def clone_with_d(self, d):
        return self.__class__(
            name=self._name,
            d={*self._d, d},
            ctx=self._ctx,
            model_command=self._model_command,
            )

    @property
    def enabled(self):
        return self._model_command.enabled

    @property
    def disabled_reason(self):
        return self._model_command.disabled_reason

    async def _run(self):
        piece = await self._model_command.run()
        if piece is None:
            return None
        if type(piece) is list:
            piece = tuple(piece)
        view_piece = visualizer(piece)
        view = view_creg.animate(view_piece, self._ctx)
        log.info("Run model command %r view: %s", self.name, view)
        self._navigator.open(self._ctx, piece, view)


@mark.service
def ui_model_command_factory():
    def _ui_model_command_factory(piece, model_state, ctx):
        model_command_pieces = [
            *global_commands(),
            *model_command_factory(piece),
            ]
        model_commands = [
            model_command_creg.animate(cmd, ctx)
            for cmd in model_command_pieces
            ]
        model_commands += enum_model_commands(piece, model_state)
        return [
            UiModelWrapperCommand.from_model_command(cmd, ctx)
            for cmd in model_commands
            ]
    return _ui_model_command_factory
