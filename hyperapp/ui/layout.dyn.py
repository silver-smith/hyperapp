import logging
from types import SimpleNamespace

from . import htypes
from .services import (
    data_to_res,
    model_command_impl_creg,
    mosaic,
    pyobj_creg,
    ui_command_factory,
    ui_command_impl_creg,
    )
from .code.command import CommandImpl, d_to_name

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
    def groups(self):
        pane_2_d = htypes.command_groups.pane_2_d()
        return {pane_2_d}

    async def run(self):
        log.info("Run layout command: %r", self.name)
        return await self._ui_command_impl.run()


@ui_command_impl_creg.actor(htypes.layout.layout_command_impl)
def layout_command_impl_from_piece(piece, ctx):
    command_ctx = ctx.controller.item_command_context(piece.item_id, piece.command_d)
    ui_command_impl = ui_command_impl_creg.invite(piece.ui_command_impl, command_ctx)
    return LayoutCommandImpl(ui_command_impl)


def layout_tree(piece, parent, controller):
    if parent is None:
        parent_id = 0
    else:
        parent_id = parent.id
    return controller.view_items(parent_id)


def _wrap_ui_command(item_id, command):
    impl = htypes.layout.layout_command_impl(
        item_id=item_id,
        command_d=command.d,
        ui_command_impl=command.impl,
        )
    return htypes.ui.ui_command(
        d=command.d,
        impl=mosaic.put(impl),
        )


def enum_layout_tree_commands(piece, current_item, controller):
    if current_item:
        item_id = current_item.id
        commands = [
            _wrap_ui_command(item_id, cmd)
            for cmd
            in controller.item_commands(item_id)
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


def _command_piece_to_item(controller, ctx, piece, item_id):
    wrapped_piece = _wrap_ui_command(item_id, piece)
    command_ctx = controller.item_command_context(item_id, piece.d)
    command = ui_command_factory(piece, command_ctx)
    wrapped_command = ui_command_factory(wrapped_piece, command_ctx)
    return htypes.layout.command_item(
        name=command.name,
        groups=', '.join(d_to_name(g) for g in command.groups),
        wrapped_groups=', '.join(d_to_name(g) for g in wrapped_command.groups),
        command_d=piece.d,
        )


def view_item_commands(piece, controller, ctx):
    command_list = [
        _command_piece_to_item(controller, ctx, command, piece.item_id)
        for command in controller.item_commands(piece.item_id)
        ]
    log.info("Get view item commands for %s: %s", piece, command_list)
    return command_list


async def add_view_command(piece, current_item):
    log.info("Add view command for %s: %s", piece, current_item)
