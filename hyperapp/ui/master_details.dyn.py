import logging

from . import htypes
from .services import (
    mark,
    mosaic,
    ui_ctl_creg,
    web,
    )
from .code.wrapper_view import WrapperView

log = logging.getLogger(__name__)


class MasterDetailsView(WrapperView):
    
    @classmethod
    def from_piece(cls, piece):
        elements = [
            htypes.box_layout.element(
                view=piece.master_view,
                stretch=piece.master_stretch,
                ),
            htypes.box_layout.element(
                view=piece.details_view,
                stretch=piece.details_stretch,
                ),
            ]
        base_piece = htypes.box_layout.view(
            direction=piece.direction,
            elements=elements,
            )
        model = web.summon(piece.model)
        base = ui_ctl_creg.animate(base_piece)
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

    def widget_state(self, widget):
        base = self._base.widget_state(widget)
        return htypes.master_details.state(
            master_state=base.elements[0],
            details_state=base.elements[1],
            )
