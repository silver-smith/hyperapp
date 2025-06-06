import logging
from functools import partial

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.view import Item, View

log = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, on_close):
        super().__init__()
        self._on_close = on_close
        self._parent_context_changed = lambda: None
        self._focused_obj = None

    def closeEvent(self, event):
        result = super().closeEvent(event)
        if event.spontaneous():
            self._on_close(self)
        return result

    def init_widget(self, parent_context_changed):
        self._parent_context_changed = parent_context_changed

    def focus_changed(self, focused_obj):
        if focused_obj is self._focused_obj:
            return
        self._focused_obj = focused_obj
        self._parent_context_changed()


class WindowView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, view_reg):
        menu_bar_view = view_reg.invite(piece.menu_bar_ref, ctx)
        central_view = view_reg.invite(piece.central_view_ref, ctx)
        return cls(menu_bar_view, central_view)

    def __init__(self, menu_bar_view, central_view):
        super().__init__()
        self._menu_bar_view = menu_bar_view
        self._central_view = central_view

    @property
    def piece(self):
        return htypes.window.view(
            menu_bar_ref=mosaic.put(self._menu_bar_view.piece),
            central_view_ref=mosaic.put(self._central_view.piece),
            )

    def construct_widget(self, state, ctx):
        w = MainWindow(self._on_close)
        central_view_state = web.summon(state.central_view_state)
        menu_bar_state = web.summon(state.menu_bar_state)
        central_widget = self._central_view.construct_widget(central_view_state, ctx)
        menu_bar = self._menu_bar_view.construct_widget(menu_bar_state, ctx)
        w.setMenuBar(menu_bar)
        w.setCentralWidget(central_widget)
        w.move(state.pos.x, state.pos.y)
        w.resize(state.size.w, state.size.h)
        return w

    def init_widget(self, widget, focusable):
        widget.init_widget(self._ctl_hook.parent_context_changed)

    def get_current(self, widget):
        return 1

    def widget_state(self, widget):
        menu_bar_state = self._menu_bar_view.widget_state(widget.menuBar())
        central_view_state = self._central_view.widget_state(widget.centralWidget())
        return htypes.window.state(
            menu_bar_state=mosaic.put(menu_bar_state),
            central_view_state=mosaic.put(central_view_state),
            size=htypes.window.size(widget.width(), widget.height()),
            pos=htypes.window.pos(widget.x(), widget.y()),
            )

    def items(self):
        return [
            Item('menu bar', self._menu_bar_view, focusable=False),
            Item('central', self._central_view),
            ]

    def item_widget(self, widget, idx):
        if idx == 0:
            return widget.menuBar()
        if idx == 1:
            return widget.centralWidget()
        return super().item_widget(widget, idx)

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        assert idx == 1  # Replacing menu bar is not yet supported.
        self._central_view = new_child_view
        widget.setCentralWidget(new_child_widget)

    def _on_close(self, w):
        log.info("Window closed: %s", w)
        self._ctl_hook.removed()
