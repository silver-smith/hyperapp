import logging

from . import htypes
from .services import (
    mark,
    model_command_creg,
    model_command_factory,
    mosaic,
    view_creg,
    visualizer,
    web,
    )
from .code.list_diff import ListDiff
from .code.view import Diff, ReplaceViewDiff
from .code.box_layout import BoxLayoutView

log = logging.getLogger(__name__)


class MasterDetailsView(BoxLayoutView):
    
    @classmethod
    def from_piece(cls, piece, ctx):
        model = web.summon(piece.model)
        master_view = view_creg.invite(piece.master_view, ctx)
        details_view = view_creg.invite(piece.details_view, ctx)
        elements = [
            cls._Element(master_view, focusable=True, stretch=piece.master_stretch),
            cls._Element(details_view, focusable=False, stretch=piece.details_stretch),
            ]
        direction = cls._direction_to_qt(piece.direction)
        return cls(direction, elements, model, piece.details_command)

    def __init__(self, direction, elements, model_piece, details_command):
        super().__init__(direction, elements)
        self._model_piece = model_piece
        self._details_command = details_command

    @property
    def piece(self):
        base = super().piece
        return htypes.master_details.view(
            model=mosaic.put(self._model_piece),
            master_view=mosaic.put(self._elements[0].view.piece),
            details_command=self._details_command,
            details_view=mosaic.put(self._elements[1].view.piece),
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

    async def child_state_changed(self, ctx, widget):
        log.info("Master-details: child state changed: %s", widget)
        master_view = super().child_view(0)
        master_widget = super().item_widget(widget, 0)
        model_state = master_view.model_state(master_widget)
        command_ctx = ctx.clone_with(
            piece=self._model_piece,
            model_state=model_state,
            **ctx.attributes(model_state),
            )
        command = model_command_creg.invite(self._details_command, command_ctx)
        piece = await command.run()
        log.info("Master-details: command result: %s", piece)
        if type(piece) is list:
            piece = tuple(piece)
        details_view_piece = visualizer(piece)
        details_view = view_creg.animate(details_view_piece, ctx)
        self.replace_element(ctx, widget, 1, details_view)

    def widget_state(self, widget):
        base = super().widget_state(widget)
        return htypes.master_details.state(
            master_state=base.elements[0],
            details_state=base.elements[1],
            )

    def model_state(self, widget):
        master_view = super().child_view(0)
        master_widget = super().item_widget(widget, 0)
        return master_view.model_state(master_widget)


@mark.ui_command(htypes.master_details.view)
def unwrap_master_details(view, state):
    log.info("Unwrap master-details: %s / %s", view, state)
    master_view = web.summon(piece.master_view)
    master_state = web.summon(state.master_state)
    return Diff(ReplaceViewDiff(master_view), master_state)


def _pick_command(model):
    command_list = model_command_factory(model)
    name_to_cmd = {
        cmd.name: cmd for cmd in command_list
        }
    preffered_names = ['open', 'details']
    for name in preffered_names:
        try:
            return name_to_cmd[name]
        except KeyError:
            pass
    return command_list[0]


@mark.ui_command
def wrap_master_details(model, piece, state):
    log.info("Wrap master-details: %s/ %s / %s", model, piece, state)
    command = _pick_command(model)
    details_adapter = htypes.str_adapter.static_str_adapter("")
    details = htypes.text.readonly_view(mosaic.put(details_adapter))
    view = htypes.master_details.view(
        model=mosaic.put(model),
        master_view=mosaic.put(piece),
        details_command=mosaic.put(command),
        details_view=mosaic.put(details),
        direction='LeftToRight',
        master_stretch=1,
        details_stretch=1,
        )
    return Diff(ReplaceViewDiff(view))
