import logging

from . import htypes
from .services import (
    mark,
    model_command_creg,
    mosaic,
    view_creg,
    visualizer,
    web,
    )
from .code.list_diff import ListDiff
from .code.view import Diff, ReplaceViewDiff
from .code.wrapper_view import WrapperView

log = logging.getLogger(__name__)


class MasterDetailsView(WrapperView):
    
    @classmethod
    def from_piece(cls, piece, ctx):
        elements = [
            htypes.box_layout.element(
                view=piece.master_view,
                focusable=True,
                stretch=piece.master_stretch,
                ),
            htypes.box_layout.element(
                view=piece.details_view,
                focusable=False,
                stretch=piece.details_stretch,
                ),
            ]
        base_piece = htypes.box_layout.view(
            direction=piece.direction,
            elements=elements,
            )
        model = web.summon(piece.model)
        base = view_creg.animate(base_piece, ctx)
        return cls(base, model, piece.details_command)

    def __init__(self, base_view, model_piece, details_command):
        super().__init__(base_view)
        self._model_piece = model_piece
        self._details_command = details_command

    @property
    def piece(self):
        base = self._base.piece
        return htypes.master_details.view(
            model=mosaic.put(self._model_piece),
            master_view=base.elements[0].view,
            details_command=self._details_command,
            details_view=base.elements[1].view,
            direction=base.direction,
            master_stretch=base.elements[0].stretch,
            details_stretch=base.elements[1].stretch,
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
        return self._base.construct_widget(base_state, ctx)

    async def child_state_changed(self, ctx, widget):
        log.info("Master-details: child state changed: %s", widget)
        master_view = self._base.child_view(0)
        master_widget = self._base.item_widget(widget, 0)
        command = model_command_creg.invite(
            self._details_command, master_view, self._model_piece, master_widget, wrappers=[])
        piece = await command.run()
        log.info("Master-details: command result: %s", piece)
        details_view_piece = visualizer(piece)
        self._ctl_hook.apply_diff(Diff(ListDiff.Replace(1, details_view_piece)))

    def widget_state(self, widget):
        base = self._base.widget_state(widget)
        return htypes.master_details.state(
            master_state=base.elements[0],
            details_state=base.elements[1],
            )

    def model_state(self, widget):
        master_view = self._base.child_view(0)
        master_widget = self._base.item_widget(widget, 0)
        return master_view.model_state(master_widget)


@mark.ui_command(htypes.master_details.view)
def unwrap_master_details(piece, state):
    log.info("Unwrap master-details: %s / %s", piece, state)
    master_view = web.summon(piece.master_view)
    master_state = web.summon(state.master_state)
    return Diff(ReplaceViewDiff(master_view), master_state)


@mark.ui_command
def wrap_master_details(piece, state):
    log.info("Wrap master-details: %s / %s", piece, state)
