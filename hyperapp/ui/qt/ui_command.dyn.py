import asyncio
import inspect
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
    'quit': 'Alt+Q',
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
    'details': 'Return',
    'open_view_item_commands': 'C',
    'add_view_command': 'Insert',
    'unwrap_master_details': 'Ctrl+U',
    'wrap_master_details': 'Ctrl+W',
    }


class CommandBase:

    def __init__(self, name, d, fn, params, model, view, widget, wrappers):
        self._name = name
        self._d = d
        self._fn = fn
        self._params = set(params)
        self._model = model  # piece
        self._view = view
        self._widget = weakref.ref(widget)
        self._wrappers = wrappers

    def __repr__(self):
        return f"{self.__class__.__name__} #{hex(id(self))[-6:]}: {self.name}"

    @property
    def d(self):
        return self._d

    @property
    def name(self):
        return self._name

    def clone_with_d(self, d):
        return self.__class__(
            name=self._name,
            d={*self._d, d},
            fn=self._fn,
            params=self._params,
            model=self._model,
            view=self._view,
            widget=self._widget(),
            wrappers=self._wrappers,
            )

    def make_action(self):
        action = QtGui.QAction(self.name, enabled=self.enabled)
        action.triggered.connect(self._start)
        if self.shortcut:
            action.setShortcut(self.shortcut)
        if not self.enabled:
            action.setToolTip(self.disabled_reason)
        return action

    def make_button(self, add_shortcut):
        text = self.name
        if self.shortcut:
            text += f' ({self.shortcut})'
        button = QtWidgets.QPushButton(
            text, focusPolicy=QtCore.Qt.NoFocus, enabled=self.enabled)
        button.pressed.connect(self._start)
        if add_shortcut and self.shortcut:
            button.setShortcut(self.shortcut)
        if not self.enabled:
            button.setToolTip(self.disabled_reason)
        return button

    @property
    def shortcut(self):
        return _hardcoded_shortcuts.get(self.name)

    def _start(self):
        log.info("Start command: %r", self.name)
        asyncio.create_task(self.run())

    @property
    def enabled(self):
        return set(self.params) >= self._params

    @property
    def disabled_reason(self):
        params = ", ".join(self._params - set(self.params))
        return f"Params not ready: {params}"

    async def run(self):
        if not self.enabled:
            log.warning("%s: Disabled: %s", self.name, self.disabled_reason)
            return
        kw = {name: value for name, value in self.params.items() if name in self._params}
        log.info("Run command: %r (%s)", self.name, kw)
        result = self._fn(**kw)
        if inspect.iscoroutinefunction(self._fn):
            result = await result
        log.info("Run command %r result: [%s] %r", self.name, type(result), result)
        if result is None:
            return None
        for wrapper in reversed(self._wrappers):
            result = wrapper(result)
        log.info("Run command %r wrapped result: [%s] %r", self.name, type(result), result)
        return result


class UiCommand(CommandBase):

    @property
    def params(self):
        params = {
            'piece': self._view.piece,
            }
        widget = self._widget()
        if widget is not None:
            params['state'] = self._view.widget_state(widget)
        if self._model is not None:
            params['model'] = self._model
        return params


@mark.service
def ui_command_factory():
    def _ui_command_factory(model, view, widget, wrappers):
        piece_t = deduce_value_type(view.piece)
        piece_t_res = pyobj_creg.reverse_resolve(piece_t)
        d_res = data_to_res(htypes.ui.ui_command_d())
        universal_d_res = data_to_res(htypes.ui.universal_ui_command_d())
        command_rec_list = [
            *association_reg.get_all((d_res, piece_t_res)),
            *association_reg.get_all(universal_d_res),
            ]
        command_list = []
        for command_rec in command_rec_list:
            command_d = pyobj_creg.invite(command_rec.d)
            fn = pyobj_creg.invite(command_rec.function)
            command_list.append(UiCommand(command_rec.name, {command_d}, fn, command_rec.params, model, view, widget, wrappers))
        return command_list
    return _ui_command_factory
