# Model commands wrapped to UI commands
# or UI commands returning model wrapped to UI commands.

import logging
from collections import namedtuple
from functools import cached_property
from operator import attrgetter, itemgetter

from . import htypes
from .services import (
    pyobj_creg,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.command import CommandKind, BoundCommandBase, UnboundCommandBase, d_to_name
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


class CustomCommands:

    def __init__(self, lcs):
        self._lcs = lcs

    @cached_property
    def command_map(self):
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
        sorted_commands = sorted(self.command_map.values(), key=attrgetter('ui_command_d'))
        command_list = htypes.command.custom_model_command_list(
            commands=tuple(mosaic.put(cmd) for cmd in sorted_commands))
        self._lcs.set(self._d, command_list)

    def set(self, command):
        ui_command_d = pyobj_creg.invite(command.ui_command_d)
        self.command_map[ui_command_d] = command
        self._save()

    def replace(self, ui_command_d, command):
        try:
            del self.command_map[ui_command_d]
        except KeyError:
            pass
        new_ui_command_d = pyobj_creg.invite(command.ui_command_d)
        self.command_map[new_ui_command_d] = command
        self._save()


class CustomModelCommands(CustomCommands):

    def __init__(self, lcs, model_t):
        super().__init__(lcs)
        self._model_t_res = pyobj_creg.actor_to_piece(model_t)

    @cached_property
    def _d(self):
        return {
            htypes.command.custom_model_commands_lcs_d(),
            self._model_t_res,
            }


class CustomGlobalCommands(CustomCommands):

    @cached_property
    def _d(self):
        return {
            htypes.command.custom_global_commands_lcs_d(),
            }
        

@mark.service
def custom_ui_model_commands(lcs, model_t):
    return CustomModelCommands(lcs, model_t)
        

@mark.service
def custom_ui_global_model_commands(lcs):
    return CustomGlobalCommands(lcs)


class CommandItem:

    def __init__(self, d, model_command_d, command, enabled=True):
        self.d = d
        self.model_command_d = model_command_d
        self.name = d_to_name(d)
        self.command = command
        self.enabled = enabled
        self.layout = command.layout

    @property
    def is_global(self):
        return self.command.properties.is_global

    @property
    def is_pure_global(self):
        if not self.command.properties.is_global:
            return False
        if self.command.properties.uses_state:
            return False
        return True


class CommandItemList:

    def __init__(
            self,
            data_to_ref,
            model_view_creg,
            visualizer,
            command_creg,
            global_model_command_reg,
            custom_commands,
            lcs,
            ):
        self._data_to_ref = data_to_ref
        self._model_view_creg = model_view_creg
        self._visualizer = visualizer
        self._command_creg = command_creg
        self._global_model_command_reg = global_model_command_reg
        self._custom_commands = custom_commands
        self._lcs = lcs
        self._d_to_item_cache = None

    @cached_property
    def _model_d_to_command(self):
        return {
            command.d: command
            for command in self._all_model_commands
            }

    @property
    def _d_to_item(self):
        if self._d_to_item_cache is not None:
            return self._d_to_item_cache
        ui_d_to_command = {}
        for model_command in self._all_model_commands:
            ui_command = wrap_model_command_to_ui_command(self._model_view_creg, self._visualizer, self._lcs, model_command)
            ui_d_to_command[ui_command.d] = ui_command
        for ui_command_d, rec in self._custom_commands.command_map.items():
            if isinstance(rec, htypes.command.custom_ui_model_command):
                model_command_d = pyobj_creg.invite(rec.model_command_d)
                try:
                    model_command = self._model_d_to_command[model_command_d]
                except KeyError:
                    log.warning("Custom model command is missing: %s", model_command_d)
                    continue
            elif isinstance(rec, htypes.command.custom_ui_command):
                model_command = self._command_creg.invite(rec.model_command)
            else:
                raise RuntimeError(f"Unexpected custom command type: {rec!r}")
            layout = web.summon_opt(rec.layout)
            ui_command = UnboundUiModelCommand(self._model_view_creg, self._visualizer, self._lcs, ui_command_d, model_command, layout)
            # Override default wrapped model_command if custom layout is configured.
            ui_d_to_command[ui_command_d] = ui_command
        self._d_to_item_cache = {
            d: CommandItem(d, command.model_command_d, command)
            for d, command in ui_d_to_command.items()
            }
        return self._d_to_item_cache

    def items(self):
        return [
            item for d, item
            in sorted(self._d_to_item.items(), key=itemgetter(0))
            ]

    def __getitem__(self, d):
        return self._d_to_item[d]

    def set_layout(self, d, layout):
        item = self._d_to_item[d]
        rec = htypes.command.custom_ui_model_command(
            ui_command_d=self._data_to_ref(d),
            model_command_d=self._data_to_ref(item.model_command_d),
            layout=mosaic.put(layout),
            )
        self._custom_commands.set(rec)
        self._d_to_item_cache = None
        return self._d_to_item[d]

    def add_custom_model_command(self, d, model_command_piece):
        rec = htypes.command.custom_ui_command(
            ui_command_d=self._data_to_ref(d),
            model_command=mosaic.put(model_command_piece),
            layout=None,
            )
        self._custom_commands.set(rec)
        self._d_to_item_cache = None
        return self._d_to_item[d]

    def rename_command(self, prev_d, new_d):
        item = self._d_to_item[prev_d]
        rec = htypes.command.custom_ui_model_command(
            ui_command_d=self._data_to_ref(new_d),
            model_command_d=self._data_to_ref(item.model_command_d),
            layout=item.layout,
            )
        self._custom_commands.replace(prev_d, rec)
        self._d_to_item_cache = None
        return self._d_to_item[new_d]


class ModelCommandItemList(CommandItemList):

    def __init__(
            self,
            data_to_ref,
            model_view_creg,
            visualizer,
            command_creg,
            global_model_command_reg,
            model_commands,
            custom_commands,
            lcs,
            ):
        super().__init__(
            data_to_ref,
            model_view_creg,
            visualizer,
            command_creg,
            global_model_command_reg,
            custom_commands,
            lcs,
            )
        self._model_commands = model_commands

    @property
    def _all_model_commands(self):
        return [*self._global_model_command_reg, *self._model_commands]


class GlobalCommandItemList(CommandItemList):

    @property
    def _all_model_commands(self):
        return self._global_model_command_reg

        
@mark.service
def ui_model_command_items(
        data_to_ref,
        model_view_creg,
        visualizer,
        command_creg,
        global_model_command_reg,
        get_model_commands,
        custom_ui_model_commands,
        lcs,
        model_t,
        ctx,
        ):
    model_commands = get_model_commands(model_t, ctx)
    custom_commands = custom_ui_model_commands(lcs, model_t)
    return ModelCommandItemList(
        data_to_ref,
        model_view_creg,
        visualizer,
        command_creg,
        global_model_command_reg,
        model_commands,
        custom_commands,
        lcs,
        )


@mark.service
def ui_global_command_items(
        data_to_ref,
        model_view_creg,
        visualizer,
        command_creg,
        global_model_command_reg,
        custom_ui_global_model_commands,
        lcs,
        ):
    custom_commands = custom_ui_global_model_commands(lcs)
    return GlobalCommandItemList(
        data_to_ref,
        model_view_creg,
        visualizer,
        command_creg,
        global_model_command_reg,
        custom_commands,
        lcs,
        )


def wrap_model_command_to_ui_command(model_view_creg, visualizer, lcs, command):
    # Layout command enumerator returns UI commands. Wrapping it (hopefully) won't cause any problems
    return UnboundUiModelCommand(model_view_creg, visualizer, lcs, command.d, command, layout=None)


@mark.service
def get_ui_model_commands(
        ui_model_command_items, lcs, model_t, ctx):
    command_item_list = ui_model_command_items(lcs, model_t, ctx)
    return [
        item.command
        for item in command_item_list.items()
        if item.enabled
        ]
