from unittest.mock import Mock, AsyncMock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import tabs


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def piece():
    label = htypes.label.view("Sample label")
    return htypes.tabs.view(
        tabs=(
            htypes.tabs.tab("One", mosaic.put(label)),
            ),
        )


@mark.fixture
def state():
    label_state = htypes.label.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(label_state),),
        )


def test_tabs(qapp, ctx, piece, state):
    view = tabs.TabsView.from_piece(piece, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state


def test_tab_list(qapp, ctx, piece, state):
    view = tabs.TabsView.from_piece(piece, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state
    tab_list = tabs.open_tab_list(view)
    assert tab_list


def test_unwrap(qapp, piece, state, ctx, view_reg):
    view = view_reg.animate(piece, ctx)
    hook = Mock()
    tabs.unwrap(view, state, hook, ctx)
    hook.replace_view.assert_called_once()


def test_wrap():
    inner = htypes.label.view("Inner label")
    piece = tabs.wrap_in_tabs(inner)
    assert isinstance(piece, htypes.tabs.view)


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config():
    k = htypes.tabs_tests.sample_k()
    factory = AsyncMock()
    factory.call.return_value = htypes.label.view("Sample label")
    return {k: factory}


@mark.fixture
def view_factory():
    k = htypes.tabs_tests.sample_k()
    return htypes.view_factory.factory(
        model=None,
        k=mosaic.put(k),
        )


@mark.fixture
def ctl_hook():
    return Mock()


@mark.fixture
def view(view_reg, piece, ctx, ctl_hook):
    view = view_reg.animate(piece, ctx)
    view.set_controller_hook(ctl_hook)
    return view


@mark.fixture.obj
def widget(view, state, ctx):
    return view.construct_widget(state, ctx)


async def test_add_element(qapp, ctx, ctl_hook, view, widget, view_factory):
    await tabs.add_element(view, widget, view_factory, ctx)
    ctl_hook.element_inserted.assert_called_once()


async def test_insert_element(qapp, ctx, ctl_hook, view, widget, view_factory):
    element_idx = 0
    await tabs.insert_element(view, widget, element_idx, view_factory, ctx)
    ctl_hook.element_inserted.assert_called_once()


def test_remove_element(qapp, ctl_hook, view, widget):
    element_idx = 0
    tabs.remove_element(view, widget, element_idx)
    ctl_hook.element_removed.assert_called_once()
