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
