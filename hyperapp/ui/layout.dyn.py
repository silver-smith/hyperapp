import logging
from types import SimpleNamespace

from . import htypes
from .code.mark import mark
from .code.command import d_to_name, BoundCommandBase, UnboundCommandBase

log = logging.getLogger(__name__)


class UnboundLayoutCommand(UnboundCommandBase):

    def __init__(self, ui_command):
        super().__init__(ui_command.d)
        self._ui_command = ui_command

    @property
    def properties(self):
        return self._ui_command.properties

    @property
    def groups(self):
        pane_2_d = htypes.command_groups.pane_2_d()
        return {pane_2_d}

    def bind(self, ctx):
        return BoundLayoutCommand(self._ui_command, self.groups)


class BoundLayoutCommand(BoundCommandBase):

    def __init__(self, ui_command, groups):
        super().__init__(ui_command.d)
        self._ui_command = ui_command
        self._groups = groups

    @property
    def name(self):
        return f'layout:{self._ui_command.name}'

    @property
    def enabled(self):
        return self._ui_command.enabled

    @property
    def disabled_reason(self):
        return self._ui_command.disabled_reason

    @property
    def groups(self):
        return self._groups

    async def run(self):
        log.info("Run layout command: %r", self.name)
        return await self._ui_command.run()


@mark.model
def layout_tree(piece, parent, controller):
    if parent is None:
        parent_id = 0
    else:
        parent_id = parent.id
    return controller.view_items(parent_id)


@mark.command_enum
def enum_layout_tree_commands(piece, current_item, controller):
    if current_item:
        item_id = current_item.id
        commands = [
            UnboundLayoutCommand(cmd)
            for cmd
            in controller.item_commands(item_id)
            ]
    else:
        commands = []
    log.info("Layout tree commands for %s: %s", current_item, commands)
    return commands


@mark.global_command
async def open_layout_tree():
    return htypes.layout.view()


@mark.command
async def open_view_item_commands(piece, current_item):
    log.info("Open view item commands for: %s", current_item)
    if current_item:
        return htypes.layout.command_list(item_id=current_item.id)


def _command_to_item(data_to_ref, controller, ctx, ui_command, item_id):
    layout_command = UnboundLayoutCommand(ui_command)
    return htypes.layout.command_item(
        name=layout_command.name,
        groups=', '.join(d_to_name(g) for g in ui_command.groups),
        wrapped_groups=', '.join(d_to_name(g) for g in layout_command.groups),
        command_d=data_to_ref(layout_command.d),
        )


@mark.command
def view_item_commands(piece, controller, ctx, data_to_ref):
    command_list = [
        _command_to_item(data_to_ref, controller, ctx, command, piece.item_id)
        for command in controller.item_commands(piece.item_id)
        ]
    log.info("Get view item commands for %s: %s", piece, command_list)
    return command_list


@mark.command
async def add_view_command(piece, current_item):
    log.info("Add view command for %s: %s", piece, current_item)
