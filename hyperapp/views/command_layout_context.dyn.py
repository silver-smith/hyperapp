from functools import cached_property

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    set_ui_model_command_layout,
    get_ui_model_commands,
    set_ui_model_commands,
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
        return cls(ctx.lcs, base_view, model, command, impl, command_d)

    def __init__(self, lcs, base_view, model, command_piece, command_impl_piece, command_d):
        super().__init__()
        self._lcs = lcs
        self._base_view = base_view
        self._model = model
        self._command_piece = command_piece
        self._command_impl_piece = command_impl_piece
        self._command_d = command_d

    @property
    def piece(self):
        return htypes.command_layout_context.view(
            base=mosaic.put(self._base_view.piece),
            model=mosaic.put(self._model),
            ui_command=mosaic.put(self._command_piece),
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
        if isinstance(self._command_impl_piece, htypes.ui.external_ui_model_command_impl):
            set_ui_model_command_layout(self._lcs, self._command_d, layout)
        else:
            self._update_command_layout(layout)

    def _update_command_layout(self, layout):
        command_list = get_ui_model_commands(self._lcs, self._model)
        idx, command = self._find_command(command_list)
        new_impl = htypes.ui.ui_model_command_impl(
            model_command_impl=self._command_impl_piece.model_command_impl,
            layout=mosaic.put(layout),
            )
        new_command = htypes.ui.command(
            d=self._command_piece.d,
            impl=mosaic.put(new_impl),
            )
        command_list = command_list.copy()
        command_list[idx] = new_command
        set_ui_model_commands(self._lcs, self._model, command_list)

    def _find_command(self, command_list):
        for idx, command in enumerate(command_list):
            if command.d == self._command_piece.d:
                return (idx, command)
        raise RuntimeError(f"Command {self._command_d} is missing from configured in LCS for model {self._model}")

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
