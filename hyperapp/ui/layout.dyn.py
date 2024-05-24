import logging

from . import htypes
from .services import (
    data_to_res,
    model_command_impl_creg,
    mosaic,
    pyobj_creg,
    ui_command_impl_creg,
    )
from .code.command import CommandKind, CommandImpl, d_res_ref_to_name

log = logging.getLogger(__name__)


class LayoutCommandImpl(CommandImpl):

    def __init__(self, ui_command_impl):
        super().__init__()
        self._ui_command_impl = ui_command_impl

    @property
    def name(self):
        return f'layout:{self._ui_command_impl.name}'

    @property
    def enabled(self):
        return self._ui_command_impl.enabled

    @property
    def disabled_reason(self):
        return self._ui_command_impl.disabled_reason

    @property
    def properties(self):
        return self._ui_command_impl.properties

    @property
    def kind(self):
        return CommandKind.MODEL

    async def run(self):
        log.info("Run layout command: %r", self.name)
        return await self._ui_command_impl.run()


@ui_command_impl_creg.actor(htypes.layout.layout_command_impl)
def layout_command_impl_from_piece(piece, ctx):
    item_id = ctx.current_item.id
    ui_command_ctx = ctx.controller.item_command_context(item_id)
    ui_command_impl = ui_command_impl_creg.invite(piece.ui_command_impl, ui_command_ctx)
    return LayoutCommandImpl(ui_command_impl)


def layout_tree(piece, parent, controller):
    if parent is None:
        parent_id = 0
    else:
        parent_id = parent.id
    return controller.view_items(parent_id)


def _wrap_ui_command(command):
    impl = htypes.layout.layout_command_impl(
        ui_command_impl=command.impl,
        )
    return htypes.ui.command(
        d=command.d,
        impl=mosaic.put(impl),
        )


def enum_layout_tree_commands(piece, current_item, controller):
    if current_item:
        commands = [
            _wrap_ui_command(cmd)
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
        htypes.layout.command_item(d_res_ref_to_name(command.d))
        for command in controller.item_commands(piece.item_id)
        ]
    log.info("Get view item commands for %s: %s", piece, command_list)
    return command_list


async def add_view_command(piece, current_item):
    log.info("Add view command for %s: %s", piece, current_item)
