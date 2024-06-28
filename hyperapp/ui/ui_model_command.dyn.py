import logging

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    deduce_t,
    enum_model_commands,
    global_commands,
    mark,
    model_command_impl_creg,
    model_commands,
    pyobj_creg,
    ui_command_impl_creg,
    model_view_creg,
    mosaic,
    visualizer,
    web,
    )
from .code.command import CommandKind, CommandImpl
from .code.command_groups import default_command_groups

log = logging.getLogger(__name__)


class UiModelCommandImpl(CommandImpl):

    def __init__(self, ctx, model_command_impl, layout, properties):
        super().__init__()
        self._ctx = ctx
        self._navigator_rec = ctx.navigator
        self._lcs = ctx.lcs
        self._model_command_impl = model_command_impl
        self._layout = layout
        self._properties = properties

    @property
    def name(self):
        return self._model_command_impl.name

    @property
    def enabled(self):
        return self._model_command_impl.enabled

    @property
    def disabled_reason(self):
        return self._model_command_impl.disabled_reason

    @property
    def properties(self):
        return self._properties

    @property
    def groups(self):
        return default_command_groups(self.properties, CommandKind.MODEL)

    async def _run(self):
        navigator_w = self._navigator_rec.widget_wr()
        if navigator_w is None:
            raise RuntimeError("Navigator widget is gone")
        piece = await self._model_command_impl.run()
        if piece is None:
            return None
        if type(piece) is list:
            piece = tuple(piece)
        if self._layout is None:
            view_piece = visualizer(self._lcs, piece)
        else:
            view_piece = self._layout
        view = model_view_creg.animate(view_piece, piece, self._ctx.pop())
        log.info("Run model command %r view: %s", self.name, view)
        self._navigator_rec.view.open(self._ctx, piece, view, navigator_w)


@ui_command_impl_creg.actor(htypes.ui.ui_model_command_impl)
def ui_model_command_impl_from_piece(piece, ctx):
    props_d_res = data_to_res(htypes.ui.command_properties_d())
    model_impl_piece = web.summon(piece.model_command_impl)
    model_impl = model_command_impl_creg.animate(model_impl_piece, ctx)
    layout = web.summon_opt(piece.layout)
    try:
        properties = association_reg[props_d_res, model_impl_piece]
    except KeyError:
        raise RuntimeError(f"Properties are missing for command {model_impl.name}: {model_impl_piece}")
    return UiModelCommandImpl(ctx, model_impl, layout, properties)


@mark.service
def set_ui_model_command_layout():
    def _set_ui_model_command_layout(lcs, command_d, layout):
        d = {
            htypes.ui.ui_model_command_layout_d(),
            command_d,
            }
        lcs.set(d, layout)
    return _set_ui_model_command_layout


def _get_ui_model_command_layout(lcs, command_d):
    d = {
        htypes.ui.ui_model_command_layout_d(),
        command_d,
        }
    return lcs.get(d)


@mark.service
def get_ui_model_command_layout():
    return _get_ui_model_command_layout


@mark.service
def set_ui_model_commands():
    def _set_ui_model_commands(lcs, model, commands):
        t = deduce_t(model)
        t_res = pyobj_creg.actor_to_piece(t)
        d = {
            htypes.ui.ui_model_command_d(),
            t_res,
            }
        value = htypes.ui.ui_model_command_list(
            commands=tuple(mosaic.put(cmd) for cmd in commands),
            )
        lcs.set(d, value)
    return _set_ui_model_commands


def _get_ui_model_commands(lcs, model):
    t = deduce_t(model)
    t_res = pyobj_creg.actor_to_piece(t)
    d = {
        htypes.ui.ui_model_command_d(),
        t_res,
        }
    value = lcs.get(d)
    if value is None:
        return []
    return [
        web.summon(ref)
        for ref in value.commands
        ]


@mark.service
def get_ui_model_commands():
    return _get_ui_model_commands


def _merge_command_lists(command_list_1, command_list_2):
    d_to_command = {
        cmd.d: cmd
        for cmd in command_list_1 + command_list_2
        }
    return list(d_to_command.values())


@mark.service
def merge_command_lists():
    return _merge_command_lists


def _model_command_to_ui_command(lcs, command):
    if isinstance(command, htypes.ui.model_command):
        command_d = pyobj_creg.invite(command.d)
        layout = _get_ui_model_command_layout(lcs, command_d)
        impl = htypes.ui.ui_model_command_impl(
            model_command_impl=command.impl,
            layout=mosaic.put_opt(layout),
            )
        impl_ref = mosaic.put(impl)
    else:
        # Layout command enumerator returns UI commands. Do not wrap them.
        impl_ref = command.impl
    return htypes.ui.command(
        d=command.d,
        impl=impl_ref,
        )


@mark.service
def list_ui_model_commands():
    def _list_ui_model_commands(lcs, piece, ctx):
        command_list = [
            *global_commands(),
            *model_commands(piece),
            *enum_model_commands(piece, ctx),
            ]
        ui_command_list = [
            _model_command_to_ui_command(lcs, cmd)
            for cmd in command_list
            ]
        lcs_command_list = _get_ui_model_commands(lcs, piece)
        return _merge_command_lists(ui_command_list, lcs_command_list)
    return _list_ui_model_commands
