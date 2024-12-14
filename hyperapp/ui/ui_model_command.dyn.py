# Model commands wrapped to UI commands
# or UI commands returning model wrapped to UI commands.

import logging
from collections import namedtuple
from functools import cached_property
from operator import attrgetter

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.command import CommandKind, BoundCommandBase, UnboundCommandBase
from .code.command_groups import default_command_groups
from .code.model_command import UnboundModelCommand

log = logging.getLogger(__name__)


class UnboundUiModelCommand(UnboundCommandBase):

    def __init__(self, model_view_creg, visualizer, lcs, d, model_command, layout=None):
        super().__init__(d)
        self._model_view_creg = model_view_creg
        self._visualizer = visualizer
        self._model_command = model_command  # Model command or UI command returning a model.
        self._layout = layout
        self._lcs = lcs

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self._model_command}>"

    @property
    def properties(self):
        return self._model_command.properties

    @property
    def groups(self):
        return default_command_groups(self._model_command.properties, CommandKind.MODEL)

    @property
    def model_command_d(self):
        return self._model_command.d

    @property
    def layout(self):
        return self._layout

    def bind(self, ctx):
        return BoundUiModelCommand(
            self._model_view_creg, self._visualizer, self._lcs, self._d, self._model_command.bind(ctx), self.groups, self._layout, ctx)


class BoundUiModelCommand(BoundCommandBase):

    def __init__(self, model_view_creg, visualizer, lcs, d, model_command, groups, layout, ctx):
        super().__init__(d)
        self._model_view_creg = model_view_creg
        self._visualizer = visualizer
        self._lcs = lcs
        self._model_command = model_command  # Model command or UI command returning a model.
        self._groups = groups
        self._layout = layout
        self._ctx = ctx
        self._navigator_rec = ctx.navigator

    @property
    def groups(self):
        return self._groups

    @property
    def enabled(self):
        return self._model_command.enabled

    @property
    def disabled_reason(self):
        return self._model_command.disabled_reason

    async def run(self):
        navigator_w = self._navigator_rec.widget_wr()
        if navigator_w is None:
            raise RuntimeError("Navigator widget is gone")
        piece = await self._model_command.run()
        if piece is None:
            return None
        if self._layout is None:
            view_piece = self._visualizer(self._lcs, piece)
        else:
            view_piece = self._layout
        view = self._model_view_creg.animate(view_piece, piece, self._ctx.pop())
        log.info("Run model command %r view: %s", self.name, view)
        self._navigator_rec.view.open(self._ctx, piece, view, navigator_w)


class CustomModelCommands:

    Rec = namedtuple('Rec', 'ui_command_d model_command layout')
    ModelRec = namedtuple('ModelRec', 'ui_command_d model_command_d layout')

    def __init__(self, lcs, model_t):
        self._lcs = lcs
        self._model_t_res = pyobj_creg.actor_to_piece(model_t)

    @cached_property
    def _d(self):
        return {
            htypes.command.custom_commands_lcs_d(),
            self._model_t_res,
            }

    @cached_property
    def _command_map(self):
        command_list = self._lcs.get(self._d)
        if not command_list:
            return {}
        result = {}
        for command_ref in command_list.commands:
            command = web.summon(command_ref)
            ui_command_d = pyobj_creg.invite(command.ui_command_d)
            result[ui_command_d] = command
        return result

    def _save(self):
        sorted_commands = sorted(self._command_map.values(), key=attrgetter('ui_command_d'))
        command_list = htypes.command.custom_model_command_list(
            commands=tuple(mosaic.put(cmd) for cmd in sorted_commands))
        self._lcs.set(self._d, command_list)

    def get_rec_list(self):
        rec_list = []
        for ui_command_d, cmd in self._command_map.items():
            if isinstance(cmd, htypes.command.custom_ui_model_command):
                rec = self.ModelRec(
                    ui_command_d=ui_command_d,
                    model_command_d=pyobj_creg.invite(cmd.model_command_d),
                    layout=cmd.layout,
                    )
            elif isinstance(cmd, htypes.command.custom_ui_command):
                rec = self.Rec(
                    ui_command_d=ui_command_d,
                    model_command=cmd.model_command,
                    layout=cmd.layout,
                    )
            else:
                raise RuntimeError(f"Unexpected custom command type: {cmd!r}")
            rec_list.append(rec)
        return rec_list

    def set(self, command):
        ui_command_d = pyobj_creg.invite(command.ui_command_d)
        self._command_map[ui_command_d] = command
        self._save()

    def replace(self, ui_command_d, command):
        try:
            del self._command_map[ui_command_d]
        except KeyError:
            pass
        new_ui_command_d = pyobj_creg.invite(command.ui_command_d)
        self._command_map[new_ui_command_d] = command
        self._save()
        

@mark.service
def custom_ui_model_commands(lcs, model_t):
    return CustomModelCommands(lcs, model_t)


def wrap_model_command_to_ui_command(model_view_creg, visualizer, lcs, command):
    # Layout command enumerator returns UI commands. Wrapping it (hopefully) won't cause any problems
    return UnboundUiModelCommand(model_view_creg, visualizer, lcs, command.d, command, layout=None)


@mark.service
def get_ui_model_commands(
        model_view_creg, visualizer, command_creg, global_model_command_reg, get_model_commands, custom_ui_model_commands,
        lcs, model, ctx):
    model_t = deduce_t(model)
    model_commands = get_model_commands(model_t, ctx)
    model_d_to_command = {
        command.d: command
        for command in model_commands
        }
    all_model_commands = [
        *global_model_command_reg,
        *model_commands,
        ]
    ui_d_to_command = {}
    for model_command in all_model_commands:
        ui_command = wrap_model_command_to_ui_command(model_view_creg, visualizer, lcs, model_command)
        ui_d_to_command[ui_command.d] = ui_command
    for rec in custom_ui_model_commands(lcs, model_t).get_rec_list():
        if isinstance(rec, CustomModelCommands.ModelRec):
            try:
                model_command = model_d_to_command[rec.model_command_d]
            except KeyError:
                log.warning("%s: Custom model command is missing: %s", model_t, model_d)
                continue
        if isinstance(rec, CustomModelCommands.Rec):
            model_command = command_creg.invite(rec.model_command)
        layout = web.summon_opt(rec.layout)
        ui_command = UnboundUiModelCommand(model_view_creg, visualizer, lcs, rec.ui_command_d, model_command, layout)
        # Override default wrapped model_command if custom layout is configured.
        ui_d_to_command[rec.ui_command_d] = ui_command
    return ui_d_to_command.values()
