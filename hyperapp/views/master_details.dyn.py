import logging

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.directory import d_to_name
from .code.box_layout import BoxLayoutView
from .code.model_command import model_command_ctx

log = logging.getLogger(__name__)


class MasterDetailsView(BoxLayoutView):
    
    @classmethod
    @mark.view
    def from_piece(cls, piece, model, ctx, view_reg, visualizer, global_model_command_reg, get_model_commands):
        model_ctx = ctx.clone_with(model=model)
        master_view = view_reg.invite(piece.master_view, model_ctx)
        details_view = view_reg.animate(htypes.label.view("Placeholder"), ctx)
        elements = [
            cls._Element(master_view, focusable=True, stretch=piece.master_stretch),
            cls._Element(details_view, focusable=False, stretch=piece.details_stretch),
            ]
        direction = cls._direction_to_qt(piece.direction)
        details_command_d = web.summon(piece.details_command_d)
        return cls(
            view_reg=view_reg,
            visualizer=visualizer,
            global_model_command_reg=global_model_command_reg,
            get_model_commands=get_model_commands,
            direction=direction,
            elements=elements,
            model=model,
            details_command_d=details_command_d,
            )

    def __init__(
            self,
            view_reg,
            global_model_command_reg,
            get_model_commands,
            visualizer,
            direction,
            elements,
            model,
            details_command_d,
            ):
        super().__init__(direction, elements)
        self._view_reg = view_reg
        self._visualizer = visualizer
        self._global_model_command_reg = global_model_command_reg
        self._get_model_commands = get_model_commands
        self._model = model
        self._details_command_d = details_command_d

    @property
    def piece(self):
        base = super().piece
        return htypes.master_details.view(
            master_view=mosaic.put(self.master_view.piece),
            details_command_d=mosaic.put(self._details_command_d),
            direction=self._direction.name,
            master_stretch=self._elements[0].stretch,
            details_stretch=self._elements[1].stretch,
            )

    def construct_widget(self, state, ctx):
        if state:
            elements = [
                state.master_state,
                state.details_state,
                ]
        else:
            elements = [
                mosaic.put(None),
                mosaic.put(None),
                ]
        base_state = htypes.box_layout.state(
            current=0,
            elements=elements,
            )
        return super().construct_widget(base_state, ctx)

    async def children_changed(self, ctx, rctx, widget):
        log.info("Master-details: children context changed: %s", widget)
        try:
            model_state = rctx.model_state
        except KeyError:
            piece = "No item is selected"
        else:
            piece = await self._run_details_command(ctx, self._model, model_state, self._details_command_d)
        details_view = self._model_to_view(ctx, piece)
        self.replace_element(ctx, widget, 1, details_view)

    async def _run_details_command(self, ctx, model, model_state, command_d):
        command_ctx = model_command_ctx(ctx, model, model_state)
        command_list = _all_model_commands(self._global_model_command_reg, self._get_model_commands, model, command_ctx)
        unbound_command = next(cmd for cmd in command_list if cmd.d == command_d)
        bound_command = unbound_command.bind(command_ctx)
        piece = await bound_command.run()
        log.info("Master-details: command result: %s", piece)
        return piece

    def _model_to_view(self, ctx, piece):
        piece_t = deduce_t(piece)
        details_view_piece = self._visualizer(ctx, piece_t)
        model_ctx = ctx.clone_with(model=piece)
        return self._view_reg.animate(details_view_piece, model_ctx)

    def widget_state(self, widget):
        base = super().widget_state(widget)
        return htypes.master_details.state(
            master_state=base.elements[0],
            details_state=base.elements[1],
            )

    @property
    def master_view(self):
        return self._elements[0].view

    @property
    def details_view(self):
        return self._elements[1].view


@mark.ui_command(htypes.master_details.view)
def unwrap_master_details(model, view, state, hook, ctx, view_reg):
    log.info("Unwrap master-details: %s / %s", view, state)
    model_ctx = ctx.clone_with(model=model)
    master_view = view_reg.invite(view.piece.master_view, model_ctx)
    master_state = web.summon(state.master_state)
    hook.replace_view(master_view, master_state)


def _all_model_commands(global_model_command_reg, get_model_commands, model_t, command_ctx):
    command_list = [
        *global_model_command_reg,
        *get_model_commands(model_t, command_ctx),
        ]
    return [
        cmd for cmd in command_list
        if not cmd.properties.is_global or cmd.properties.uses_state
        ]

    
def _pick_command(global_model_command_reg, get_model_commands, model_t, command_ctx):
    command_list = _all_model_commands(global_model_command_reg, get_model_commands, model_t, command_ctx)
    name_to_cmd = {
        d_to_name(cmd.d): cmd for cmd in command_list
        }
    preffered_names = ['open', 'details']
    for name in preffered_names:
        try:
            return name_to_cmd[name]
        except KeyError:
            pass
    return command_list[0]  # Pick any.


@mark.view_factory
def master_details(model, model_state, inner, ctx, global_model_command_reg, get_model_commands):
    log.info("Wrap master-details: %s / %s", model, inner)
    command_ctx = model_command_ctx(ctx, model, model_state)
    model_t = deduce_t(model)
    command = _pick_command(global_model_command_reg, get_model_commands, model_t, command_ctx)
    return htypes.master_details.view(
        master_view=mosaic.put(inner),
        details_command_d=mosaic.put(command.d),
        direction='LeftToRight',
        master_stretch=1,
        details_stretch=1,
        )
