from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import label


def test_label(qapp):
    ctx = Context()
    piece = htypes.label.view("Sample label")
    state = htypes.label.state()

    view = label.LabelView.from_piece(piece, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state


def test_factory():
    piece = label.label_view()
    assert piece
