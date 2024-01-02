from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from PySide6 import QtWidgets

from . import htypes
from .tested.code import list
from .services import (
    mosaic,
    types,
    )
from .code.context import Context


def make_adapter_layout():
    value = [
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        ]
    t = deduce_complex_value_type(mosaic, types, value)
    return htypes.list_adapter.static_list_adapter(mosaic.put(value, t))


def make_layout():
    adapter_layout = make_adapter_layout()
    return htypes.list.layout(mosaic.put(adapter_layout))


def test_list():
    ctx = Context()
    layout = make_layout()
    state = None
    app = QtWidgets.QApplication()
    try:
        ctl = list.ListCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        state = ctl.widget_state(widget)
        # assert state
    finally:
        app.shutdown()
