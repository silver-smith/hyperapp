import logging

from . import htypes
from .services import (
    data_to_res,
    mosaic,
    )

log = logging.getLogger(__name__)


def layout_tree(piece, parent, controller):
    if parent is None:
        parent_id = 0
    else:
        parent_id = parent.id
    return controller.view_items(parent_id)


def _copy_command_with_d(command, d):
    d_res = data_to_res(d)
    command_d = (
        *command.d,
        mosaic.put(d_res),
        )
    if isinstance(command, htypes.ui.ui_command):
        return htypes.ui.ui_command(
            d=command_d,
            name=command.name,
            function=command.function,
            params=command.params,
            )
    if isinstance(command, htypes.ui.ui_model_command):
        return htypes.ui.ui_command(
            d=command_d,
            name=command.name,
            model_command=command.model_command,
            )
    raise RuntimeError(f"Unsupported command type: {command}")


def layout_tree_commands(piece, current_item, controller):
    context_kind_d = htypes.ui.context_model_command_kind_d()
    if current_item:
        commands = [
            _copy_command_with_d(cmd, context_kind_d)
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
