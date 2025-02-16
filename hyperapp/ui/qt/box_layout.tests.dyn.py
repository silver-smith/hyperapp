from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import box_layout


@mark.fixture
def piece():
    label_1 = htypes.label.view("Sample label 1")
    label_2 = htypes.label.view("Sample label 2")
    return htypes.box_layout.view(
        direction='LeftToRight',
        elements=[
            htypes.box_layout.element(
                view=mosaic.put(label_1),
                focusable=True,
                stretch=1,
                ),
            htypes.box_layout.element(
                view=mosaic.put(label_2),
                focusable=False,
                stretch=2,
                ),
            ],
        )


@mark.fixture
def state():
    label_state = htypes.label.state()
    return htypes.box_layout.state(
        current=0,
        elements=[
            mosaic.put(label_state),
            mosaic.put(label_state),
            ],
        )


@mark.fixture
def ctx():
    return Context()


def test_box_layout(qapp, piece, state, ctx):
    view = box_layout.BoxLayoutView.from_piece(piece, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state


def test_unwrap(qapp, piece, state, ctx, view_reg):
    view = view_reg.animate(piece, ctx)
    hook = Mock()
    box_layout.unwrap(view, state, hook, ctx)
    hook.replace_view.assert_called_once()


def test_wrap():
    inner = htypes.label.view("Inner label")
    piece = box_layout.wrap(inner)
    assert isinstance(piece, htypes.box_layout.view)
