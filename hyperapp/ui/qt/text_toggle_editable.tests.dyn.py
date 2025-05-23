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
    accessor = htypes.accessor.model_accessor()
    cvt = htypes.type_convertor.noop_convertor()
    return htypes.value_adapter.value_adapter(
        accessor=mosaic.put(accessor),
        convertor=mosaic.put(cvt),
        )


@mark.fixture
def view_piece(adapter):
    return htypes.text.readonly_view(
        adapter=mosaic.put(adapter),
        )


@mark.fixture
def edit_piece(adapter):
    return htypes.text.edit_view(
        adapter=mosaic.put(adapter),
        )


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


def test_readonly_to_edit(qapp, view_reg, view_piece, state, model, ctx, hook):
    view = view_reg.animate(view_piece, ctx)
    text_toggle_editable.toggle_editable(model, view, hook, ctx)
    hook.replace_view.assert_called_once()


def test_edit_to_readonly(qapp, view_reg, edit_piece, model, ctx, hook):
    view = view_reg.animate(edit_piece, ctx)
    text_toggle_editable.toggle_editable(model, view, hook, ctx)
    hook.replace_view.assert_called_once()
