import logging

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.command import d_to_name
from .code.box_layout import BoxLayoutView

log = logging.getLogger(__name__)


def _make_command_ctx(ctx, model, model_state):
    return ctx.push(
        model=model,
        piece=model,
        model_state=model_state,
        **ctx.attributes(model_state),
        )


class MasterDetailsView(BoxLayoutView):
    
    @classmethod
    @mark.actor.model_view_creg
    def from_piece(cls, piece, model, ctx, data_to_ref, view_creg, model_view_creg, visualizer):
        master_view = model_view_creg.invite(piece.master_view, model, ctx)
        details_view = view_creg.animate(htypes.label.view("Placeholder"), ctx)
        elements = [
            cls._Element(master_view, focusable=True, stretch=piece.master_stretch),
            cls._Element(details_view, focusable=False, stretch=piece.details_stretch),
            ]
        direction = cls._direction_to_qt(piece.direction)
        details_command_d = web.summon(piece.details_command_d)
        return cls(data_to_ref, model_view_creg, visualizer, direction, elements, model, details_command_d)

    def __init__(self, data_to_ref, model_view_creg, visualizer, direction, elements, model, details_command_d):
        super().__init__(direction, elements)
        self._data_to_ref = data_to_ref
        self._model_view_creg = model_view_creg
        self._visualizer = visualizer
        self._model = model
        self._details_command_d = details_command_d

    @property
    def piece(self):
        base = super().piece
        return htypes.master_details.view(
            master_view=mosaic.put(self.master_view.piece),
            details_command_d=self._data_to_ref(self._details_command_d),
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

    async def children_context_changed(self, ctx, rctx, widget):
        log.info("Master-details: children context changed: %s", widget)
        try:
            model_state = rctx.model_state
        except KeyError:
            piece = "No item is selected"
        else:
            piece = await self.run_details_command(ctx, self._model, model_state, self._details_command_d)
        details_view = self.model_to_view(ctx, piece)
        self.replace_element(ctx, widget, 1, details_view)

    @staticmethod
    async def run_details_command(ctx, model, model_state, command_d):
        command_ctx = _make_command_ctx(ctx, model, model_state)
        command_list = get_ui_model_commands(lcs, model, command_ctx)
        unbound_command = next(cmd for cmd in command_list if cmd.d == command_d)
        bound_command = unbound_command.bind(command_ctx)
        piece = await bound_command.run()
        log.info("Master-details: command result: %s", piece)
        return piece

    @staticmethod
    def model_to_view(ctx, piece):
        details_view_piece = self._visualizer(ctx.lcs, piece)
        return self._model_view_creg.animate(details_view_piece, piece, ctx)

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
def unwrap_master_details(model, view, state, hook, ctx, model_view_creg):
    log.info("Unwrap master-details: %s / %s", view, state)
    master_view = model_view_creg.invite(view.piece.master_view, model, ctx)
    master_state = web.summon(state.master_state)
    hook.replace_view(master_view, master_state)


def _pick_command(get_ui_model_commands, lcs, model, command_ctx):
    command_list = get_ui_model_commands(lcs, model, command_ctx)
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


@mark.universal_ui_command
def wrap_master_details(model, model_state, view, hook, lcs, ctx, data_to_ref, model_view_creg, get_ui_model_commands):
    log.info("Wrap master-details: %s / %s", model, view)
    command_ctx = _make_command_ctx(ctx, model, model_state)
    command = _pick_command(get_ui_model_commands, lcs, model, command_ctx)
    view_piece = htypes.master_details.view(
        master_view=mosaic.put(view.piece),
        details_command_d=data_to_ref(command.d),
        direction='LeftToRight',
        master_stretch=1,
        details_stretch=1,
        )
    new_view = model_view_creg.animate(view_piece, model, ctx)
    hook.replace_view(new_view)
