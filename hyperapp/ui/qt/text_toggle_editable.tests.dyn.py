from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import text_toggle_editable


@mark.fixture
def adapter():
    return htypes.str_adapter.static_str_adapter()


@mark.fixture
def readonly_piece(adapter):
    return htypes.text.readonly_view(mosaic.put(adapter))


@mark.fixture
def edit_piece(adapter):
    return htypes.text.edit_view(mosaic.put(adapter))


@mark.fixture
def state():
    return htypes.text.state('')


@mark.fixture
def model():
    return "Sample text"


@mark.fixture
def ctx(model):
    return Context(
        model=model,
        )


@mark.fixture
def hook():
    return Mock()


def test_readonly_to_edit(qapp, view_reg, readonly_piece, state, model, ctx, hook):
    view = view_reg.animate(readonly_piece, ctx)
    text_toggle_editable.toggle_editable(model, view, hook, ctx)
    hook.replace_view.assert_called_once()


def test_edit_to_readonly(qapp, view_reg, edit_piece, model, ctx, hook):
    view = view_reg.animate(edit_piece, ctx)
    text_toggle_editable.toggle_editable(model, view, hook, ctx)
    hook.replace_view.assert_called_once()
