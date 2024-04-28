from PySide6 import QtWidgets

from . import htypes
from .services import (
    data_to_res,
    fn_to_res,
    mark,
    mosaic,
    )
from .code.context import Context
from .tested.code import master_details


def _details_command_impl(piece):
    return f"Details for: {piece}"


def _details_command():
    return htypes.ui.model_command(
        d=(mosaic.put(data_to_res(htypes.master_details_tests.sample_details_command_d())),),
        name='details',
        function=mosaic.put(fn_to_res(_details_command_impl)),
        params=('piece',),
        )


def make_piece():
    model = "Sample master text"
    master_adapter = htypes.str_adapter.static_str_adapter(model)
    details_adapter= htypes.str_adapter.static_str_adapter("Sample details")
    master = htypes.text.readonly_view(mosaic.put(master_adapter))
    details = htypes.text.readonly_view(mosaic.put(details_adapter))
    command = _details_command()
    return htypes.master_details.view(
        model=mosaic.put(model),
        master_view=mosaic.put(master),
        details_command=mosaic.put(command),
        details_view=mosaic.put(details),
        direction='LeftToRight',
        master_stretch=1,
        details_stretch=1,
        )


def make_state():
    text_state = htypes.text.state()
    return htypes.master_details.state(
        master_state=mosaic.put(text_state),
        details_state=mosaic.put(text_state),
        )


def test_master_details():
    ctx = Context()
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = master_details.MasterDetailsView.from_piece(piece, ctx)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


@mark.service
def model_command_factory():
    def _factory(model):
        return [_details_command()]
    return _factory


def test_wrap_master_details():
    ctx = Context()
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = master_details.MasterDetailsView.from_piece(piece, ctx)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
        model = "Sample model"
        master_details.wrap_master_details(model, view, state)
    finally:
        app.shutdown()
