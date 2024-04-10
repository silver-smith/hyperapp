import asyncio
import logging
import weakref
from functools import cached_property

from PySide6 import QtCore, QtGui, QtWidgets

from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    mark,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


_hardcoded_shortcuts = {
    'go_back': 'Esc',
    'go_forward': 'Alt+Right',
    'duplicate_tab': 'Shift+f4',
    'close_tab': 'Ctrl+f4',
    'duplicate_window': 'Alt+W',
    'open_layout_tree': 'Alt+L',
    'open_sample_static_text_1': 'f1',
    'open_sample_static_text_2': 'f2',
    'open_sample_static_list': 'f3',
    'open_sample_fn_list': 'f4',
    'open_sample_fn_tree': 'f6',
    'open_feed_sample_fn_list': 'f5',
    'open_feed_sample_fn_tree': 'Shift+f6',
    'show_state': 'Ctrl+Return',
    'sample_list_state': 'Return',
    'open_view_item_commands': 'C',
    'add_view_command': 'Insert',
    'unwrap_master_details': 'Ctrl+U',
    }


class CommandBase:

    def __init__(self, name, fn, view, widget, wrappers):
        self._name = name
        self._fn = fn
        self._view = view
        self._widget = weakref.ref(widget)
        self._wrappers = wrappers

    def __repr__(self):
        return f"{self.__class__.__name__} #{hex(id(self))[-6:]}: {self.name}"

    @property
    def name(self):
        return self._name

    def make_action(self):
        action = QtGui.QAction(self.name)
        action.triggered.connect(self._start)
        if self.shortcut:
            action.setShortcut(self.shortcut)
        return action

    def make_button(self):
        text = self.name
        if self.shortcut:
            text += f' ({self.shortcut})'
        button = QtWidgets.QPushButton(text, focusPolicy=QtCore.Qt.NoFocus)
        button.pressed.connect(self._start)
        # if self.shortcut:
        #     button.setShortcut(self.shortcut)
        return button

    @property
    def shortcut(self):
        return _hardcoded_shortcuts.get(self.name)

    def _start(self):
        log.info("Start command: %r", self.name)
        asyncio.create_task(self.run())


class UiCommand(CommandBase):

    async def run(self):
        widget = self._widget()
        if widget is None:
            log.warning("Not running UI command %r: Widget is gone", self._name)
            return None
        piece = self._view.piece
        state = self._view.widget_state(widget)
        log.info("Run ui command: %r (%s, %s)", self._name, piece, state)
        result = self._fn(piece, state)
        log.info("Run ui command %r result: [%s] %r", self._name, type(result), result)
        if result is None:
            return None
        for wrapper in reversed(self._wrappers):
            result = wrapper(result)
        log.info("Run ui command %r wrapped result: [%s] %r", self._name, type(result), result)
        return result


@mark.service
def ui_command_factory():
    def _ui_command_factory(view, widget, wrappers):
        piece_t = deduce_value_type(view.piece)
        piece_t_res = pyobj_creg.reverse_resolve(piece_t)
        d_res = data_to_res(htypes.ui.ui_command_d())
        universal_d_res = data_to_res(htypes.ui.universal_ui_command_d())
        fn_res_list = [
            *association_reg.get_all((d_res, piece_t_res)),
            *association_reg.get_all(universal_d_res),
            ]
        command_list = []
        for fn_res in fn_res_list:
            fn = pyobj_creg.animate(fn_res)
            command_list.append(UiCommand(fn.__name__, fn, view, widget, wrappers))
        return command_list
    return _ui_command_factory
