# Model commands wrapped to UI commands
# or UI commands returning model wrapped to UI commands.

import logging
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

    def __init__(self, model_view_creg, visualizer, lcs, model_command, layout):
        super().__init__(model_command.d)
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

    def bind(self, ctx):
        return BoundUiModelCommand(
            self._model_view_creg, self._visualizer, self._lcs, self._model_command.bind(ctx), self.groups, self._layout, ctx)


class BoundUiModelCommand(BoundCommandBase):

    def __init__(self, model_view_creg, visualizer, lcs, model_command, groups, layout, ctx):
        super().__init__(model_command.d)
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


# @ui_command_impl_creg.actor(htypes.ui.ui_model_command_impl)
# @ui_command_impl_creg.actor(htypes.ui.external_ui_model_command_impl)
# def ui_model_command_impl_from_piece(piece, ctx):
#     model_impl = model_command_impl_creg.invite(piece.model_command_impl, ctx)
#     layout = web.summon_opt(piece.layout)
#     return UiModelCommandImpl(ctx, model_impl, layout, model_impl.properties)


# @mark.service
# def set_ui_model_command_layout():
#     def _set_ui_model_command_layout(lcs, command_d, layout):
#         d = {
#             htypes.ui.ui_model_command_layout_d(),
#             command_d,
#             }
#         lcs.set(d, layout)
#     return _set_ui_model_command_layout


# def _get_ui_model_command_layout(lcs, command_d):
#     d = {
#         htypes.ui.ui_model_command_layout_d(),
#         command_d,
#         }
#     return lcs.get(d)


# @mark.service
# def get_ui_model_command_layout():
#     return _get_ui_model_command_layout


class CustomModelCommands:

    def __init__(self, lcs, model_t):
        self._lcs = lcs
        self._model_t_res = pyobj_creg.actor_to_piece(model_t)
        self._ui_d_to_command = {}

    @cached_property
    def _d(self):
        return {
            htypes.command.ui_model_command_d(),
            self._model_t_res,
            }

    @cached_property
    def _command_map(self):
        command_list = self._lcs.get(self._d)
        if not command_list:
            return {}
        command_pieces = [
            web.summon(cmd) for cmd in command_list.commands
            ]
        return {
            cmd.ui_command_d: cmd
            for cmd in command_pieces
            }

    def _save(self):
        sorted_commands = sorted(self._command_map.values(), key=attrgetter('ui_command_d'))
        command_list = htypes.command.custom_model_command_list(
            commands=tuple(mosaic.put(cmd) for cmd in sorted_commands))
        self._lcs.set(self._d, command_list)

    def set(self, command):
        self._command_map[command.ui_command_d] = command
        self._save()
        

@mark.service
def custom_ui_model_commands(lcs, model_t):
    return CustomModelCommands(lcs, model_t)


# @mark.service
# def get_ui_model_command(lcs, model_t, model_command_d):
#     model_t_res = pyobj_creg.actor_to_piece(model_t)
#     d = {
#         htypes.command.ui_model_command_d(),
#         model_t_res,
#         }


# @mark.service
# def set_ui_model_commands():
#     return _set_ui_model_commands


# def _get_ui_model_commands(lcs, model):
#     t = deduce_t(model)
#     t_res = pyobj_creg.actor_to_piece(t)
#     d = {
#         htypes.ui.ui_model_command_d(),
#         t_res,
#         }
#     value = lcs.get(d)
#     if value is None:
#         return []
#     return [
#         web.summon(ref)
#         for ref in value.commands
#         ]


# @mark.service
# def get_ui_model_commands():
#     return _get_ui_model_commands


# def change_command(lcs, model, command_d_ref, change_fn):
#     assert False, "TODO"

#     def find_command(command_list):
#         for idx, command in enumerate(command_list):
#             if command.d == command_d_ref:
#                 return (idx, command)
#         d = pyobj_creg.invite(command_d_ref)
#         raise RuntimeError(f"Command {d} is missing from configured in LCS for model {model}")

#     command_list = _get_ui_model_commands(lcs, model)
#     idx, command = find_command(command_list)
#     new_command = change_fn(command)
#     command_list = command_list.copy()
#     command_list[idx] = new_command
#     _set_ui_model_commands(lcs, model, command_list)


# def _merge_command_lists(command_list_1, command_list_2):
#     d_to_command = {
#         cmd.d: cmd
#         for cmd in command_list_1 + command_list_2
#         }
#     return list(d_to_command.values())


# @mark.service
# def merge_command_lists():
#     return _merge_command_lists


def wrap_model_command_to_ui_command(model_view_creg, visualizer, lcs, command):
    # Layout command enumerator returns UI commands. Wrapping it (hopefully) won't cause any problems
    # layout = _get_ui_model_command_layout(lcs, command_d)
    return UnboundUiModelCommand(model_view_creg, visualizer, lcs, command, layout=None)


@mark.service
def get_ui_model_commands(model_view_creg, visualizer, global_model_command_reg, get_model_commands, lcs, model, ctx):
    model_command_list = [
        *global_model_command_reg,
        *get_model_commands(model, ctx),
        ]
    ui_command_list = [
        wrap_model_command_to_ui_command(model_view_creg, visualizer, lcs, cmd)
        for cmd in model_command_list
        ]
    # lcs_command_list = _get_ui_model_commands(lcs, piece)
    # return _merge_command_lists(ui_command_list, lcs_command_list)
    return ui_command_list
