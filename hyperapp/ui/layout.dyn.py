import logging

from . import htypes
from .services import (
    data_to_res,
    model_command_creg,
    mosaic,
    pyobj_creg,
    ui_command_creg,
    )
from .code.command import CommandBase

log = logging.getLogger(__name__)


class LayoutCommand(CommandBase):

    def __init__(self, name, d, ui_command):
        super().__init__(name, d)
        self._ui_command = ui_command

    @property
    def enabled(self):
        return self._ui_command.enabled

    @property
    def disabled_reason(self):
        return self._ui_command.disabled_reason

    async def _run(self):
        log.info("Run layout command: %r", self.name)
        return await self._ui_command.run()


@model_command_creg.actor(htypes.layout.layout_command)
def layout_command_from_piece(piece, ctx):
    command_d = {pyobj_creg.invite(d) for d in piece.d}
    item_id = ctx.current_item.id
    ui_command_ctx = ctx.controller.item_command_context(item_id)
    ui_command = ui_command_creg.invite(piece.ui_command, ui_command_ctx)
    return LayoutCommand(piece.name, command_d, ui_command)


def layout_tree(piece, parent, controller):
    if parent is None:
        parent_id = 0
    else:
        parent_id = parent.id
    return controller.view_items(parent_id)


def _wrap_ui_command(command, kind_d_res_ref):
    return htypes.layout.layout_command(
        name=command.name,
        d=(
            command.d[0],
            kind_d_res_ref,
            ),
        ui_command=mosaic.put(command),
        )


def enum_layout_tree_commands(piece, current_item, controller):
    kind_d = htypes.ui.context_model_command_kind_d()
    kind_d_res_ref = mosaic.put(data_to_res(kind_d))
    if current_item:
        commands = [
            _wrap_ui_command(cmd, kind_d_res_ref)
            for cmd
            in controller.item_commands(current_item.id)
            ]
    else:
        commands = []
    log.info("Layout tree commands for %s: %s", current_item, commands)
    return commands


async def open_layout_tree():
    return htypes.layout.view()


async def open_view_item_commands(piece, current_item):
    log.info("Open view item commands for: %s", current_item)
    if current_item:
        return htypes.layout.command_list(item_id=current_item.id)


def view_item_commands(piece, controller):
    command_list = [
        htypes.layout.command_item(command.name)
        for command in controller.item_commands(piece.item_id)
        ]
    log.info("Get view item commands for %s: %s", piece, command_list)
    return command_list


async def add_view_command(piece, current_item):
    log.info("Add view command for %s: %s", piece, current_item)
