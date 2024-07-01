from functools import cached_property

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    set_ui_model_command_layout,
    view_creg,
    web,
    )
from .code.view import Item, View


class CommandLayoutContextView(View):

    @classmethod
    def from_piece(cls, piece, ctx):
        base_view = view_creg.invite(piece.base, ctx)
        model = web.summon(piece.model)
        command = web.summon(piece.ui_command)
        impl = web.summon(command.impl)
        command_d = pyobj_creg.invite(command.d)
        return cls(ctx.lcs, base_view, model, piece.ui_command, impl, command_d)

    def __init__(self, lcs, base_view, model, ui_command_ref, command_impl, command_d):
        super().__init__()
        self._lcs = lcs
        self._base_view = base_view
        self._model = model
        self._ui_command_ref = ui_command_ref
        self._command_impl = command_impl  # piece
        self._command_d = command_d

    @property
    def piece(self):
        return htypes.command_layout_context.view(
            base=mosaic.put(self._base_view.piece),
            model=mosaic.put(self._model),
            ui_command=self._ui_command_ref,
            )

    def construct_widget(self, state, ctx):
        if state is not None:
            base_state = web.summon(state.base)
        else:
            base_state = None
        base_widget = self._base_view.construct_widget(base_state, ctx)
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.Direction.TopToBottom, widget)
        layout.addWidget(QtWidgets.QLabel(text="Command layout"))
        layout.addWidget(base_widget)
        return widget

    def _set_layout(self, layout):
        command_d = self._command_d
        set_ui_model_command_layout(self._lcs, command_d, layout)

    def children_context(self, ctx):
        return ctx.clone_with(
            set_layout=self._set_layout,
            )

    def get_current(self, widget):
        return 0

    def widget_state(self, widget):
        base_widget = self._base_widget(widget)
        base_state = self._base_view.widget_state(base_widget)
        return htypes.command_layout_context.state(
            base=mosaic.put(base_state),
            )

    def replace_child_widget(self, widget, idx, new_child_widget):
        if idx != 0:
            return super().replace_child_widget(widget, idx, new_child_widget)
        layout = widget.layout()
        old_w = layout.itemAt(1).widget()
        layout.replaceWidget(old_w, new_child_widget)
        old_w.deleteLater()

    def items(self):
        return [Item('base', self._base_view)]

    def item_widget(self, widget, idx):
        if idx == 0:
            return self._base_widget(widget)
        return super().item_widget(widget, idx)

    def _base_widget(self, widget):
        layout = widget.layout()
        return layout.itemAt(1).widget()


def open_command_layout_context(piece, current_item, navigator, ctx):
    new_view_piece = htypes.command_layout_context.view(
        base=mosaic.put(navigator.view.piece),
        model=piece.model,
        ui_command=current_item.command,
        )
    new_state = htypes.command_layout_context.state(
        base=mosaic.put(navigator.state),
        )
    new_view = view_creg.animate(new_view_piece, ctx)
    navigator.hook.replace_view(new_view, new_state)
